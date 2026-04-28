import os
import random
import string
from datetime import datetime

import redis
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# ── App setup ──────────────────────────────────────────────
app = FastAPI(
    title="URL Shortener",
    description="A DevOps learning project — Phase 3",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus metrics ──────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"]
)
REDIRECT_COUNT = Counter(
    "url_redirects_total",
    "Total URL redirects"
)
URL_CREATED = Counter(
    "urls_created_total",
    "Total URLs created"
)

# ── DB & Redis connections ──────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "urlshortener"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "secret"),
    )

def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=6379,
        decode_responses=True
    )

def init_db():
    """Tạo table nếu chưa có"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            click_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# ── Models ──────────────────────────────────────────────────
class ShortenRequest(BaseModel):
    url: str
    custom_code: str = None  # tuỳ chọn: tự đặt short code

class URLResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: str

# ── Helper ──────────────────────────────────────────────────
def generate_code(length=6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

# ── Middleware: đo latency ──────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    return response

# ── Startup ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    # Retry vì DB có thể chưa sẵn sàng ngay
    for i in range(10):
        try:
            init_db()
            print("✅ Database connected & initialized")
            break
        except Exception as e:
            print(f"⏳ Waiting for DB... ({i+1}/10): {e}")
            time.sleep(2)

# ── Routes ──────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    """Trang chủ đơn giản"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>URL Shortener | Premium</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #8b5cf6;
                --primary-hover: #7c3aed;
                --bg: #0f172a;
                --glass-bg: rgba(30, 41, 59, 0.7);
                --glass-border: rgba(255, 255, 255, 0.1);
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
            }
            body {
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 0;
                background-color: var(--bg);
                background-image: 
                    radial-gradient(at 0% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
                    radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.15) 0px, transparent 50%);
                color: var(--text-main);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                width: 100%;
                max-width: 500px;
                padding: 2.5rem 2rem;
                margin: 1rem;
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid var(--glass-border);
                border-radius: 24px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                transform: translateY(0);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .container:hover {
                transform: translateY(-5px);
                box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.6);
            }
            h1 {
                margin: 0 0 0.5rem 0;
                font-size: 2rem;
                font-weight: 700;
                text-align: center;
                background: linear-gradient(to right, #a78bfa, #38bdf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p.subtitle {
                text-align: center;
                color: var(--text-muted);
                margin-bottom: 2rem;
                font-size: 0.95rem;
            }
            .input-group {
                margin-bottom: 1.25rem;
            }
            input {
                width: 100%;
                padding: 1rem 1.25rem;
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                color: var(--text-main);
                font-size: 1rem;
                font-family: inherit;
                box-sizing: border-box;
                transition: all 0.2s ease;
            }
            input:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
            }
            input::placeholder {
                color: #64748b;
            }
            button.btn {
                width: 100%;
                padding: 1rem;
                background: var(--primary);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 1rem;
                font-weight: 600;
                font-family: inherit;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
            }
            button.btn:hover {
                background: var(--primary-hover);
                transform: scale(1.02);
            }
            button.btn:active {
                transform: scale(0.98);
            }
            #result-card {
                margin-top: 1.5rem;
                padding: 1.25rem;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.2);
                border-radius: 12px;
                display: none;
                animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            }
            @keyframes slideDown {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .result-label {
                font-size: 0.85rem;
                color: #34d399;
                font-weight: 600;
                margin-bottom: 0.5rem;
                display: block;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .result-url {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            .result-url a {
                color: var(--text-main);
                text-decoration: none;
                font-weight: 500;
                word-break: break-all;
                flex-grow: 1;
                font-size: 1.1rem;
                transition: color 0.2s;
            }
            .result-url a:hover {
                color: #a78bfa;
            }
            .copy-btn {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 0.5rem;
                border-radius: 8px;
                color: var(--text-main);
                cursor: pointer;
                transition: background 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .copy-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            .error {
                color: #f87171;
                font-size: 0.9rem;
                margin-top: 1rem;
                text-align: center;
                display: none;
                animation: shake 0.4s ease-in-out;
            }
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            @keyframes spin { 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔗 URL Shortener</h1>
            <p class="subtitle">Fast, secure, and beautiful link management.</p>
            
            <div class="input-group">
                <input type="url" id="url" placeholder="Paste your long URL here (http://...)" required autocomplete="off" />
            </div>
            
            <div class="input-group">
                <input type="text" id="code" placeholder="Custom code (optional, e.g., my-link)" autocomplete="off" maxlength="10" />
            </div>
            
            <button class="btn" id="submit-btn" onclick="shorten()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                Shorten URL
            </button>
            
            <div id="error-msg" class="error"></div>
            
            <div id="result-card">
                <span class="result-label">Your Short URL:</span>
                <div class="result-url">
                    <a id="short" href="#" target="_blank"></a>
                    <button class="copy-btn" onclick="copyToClipboard()" title="Copy to clipboard">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                </div>
            </div>
        </div>

        <script>
            async function shorten() {
                const urlInput = document.getElementById('url');
                const codeInput = document.getElementById('code');
                const submitBtn = document.getElementById('submit-btn');
                const resultCard = document.getElementById('result-card');
                const errorMsg = document.getElementById('error-msg');
                const shortLink = document.getElementById('short');
                
                const url = urlInput.value.trim();
                const code = codeInput.value.trim();
                
                errorMsg.style.display = 'none';
                resultCard.style.display = 'none';
                
                if (!url) {
                    showError('Vui lòng nhập URL!');
                    urlInput.focus();
                    return;
                }
                if (!url.startsWith('http://') && !url.startsWith('https://')) {
                    showError('URL phải bắt đầu bằng http:// hoặc https://');
                    urlInput.focus();
                    return;
                }

                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="4.93" x2="19.07" y2="7.76"></line></svg> Processing...';
                submitBtn.disabled = true;

                try {
                    const body = { url };
                    if (code) body.custom_code = code;
                    
                    const res = await fetch('/shorten', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    
                    const data = await res.json();
                    
                    if (res.ok) {
                        shortLink.href = data.short_url;
                        shortLink.innerText = data.short_url;
                        resultCard.style.display = 'block';
                        codeInput.value = '';
                    } else {
                        showError(data.detail || 'Đã có lỗi xảy ra!');
                    }
                } catch (err) {
                    showError('Không thể kết nối đến server!');
                } finally {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }

            function showError(msg) {
                const errorMsg = document.getElementById('error-msg');
                errorMsg.innerText = msg;
                errorMsg.style.display = 'block';
                errorMsg.style.animation = 'none';
                errorMsg.offsetHeight; 
                errorMsg.style.animation = 'shake 0.4s ease-in-out';
            }

            async function copyToClipboard() {
                const text = document.getElementById('short').innerText;
                try {
                    await navigator.clipboard.writeText(text);
                    const copyBtn = document.querySelector('.copy-btn');
                    const originalHTML = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                    setTimeout(() => {
                        copyBtn.innerHTML = originalHTML;
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy', err);
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/shorten", response_model=URLResponse)
def shorten_url(body: ShortenRequest, request: Request):
    """Tạo short URL mới"""
    # Validate URL thô
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL phải bắt đầu bằng http:// hoặc https://")

    if body.custom_code and len(body.custom_code) > 10:
        raise HTTPException(status_code=400, detail="Custom code không được dài quá 10 ký tự!")

    short_code = body.custom_code if body.custom_code else generate_code()

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO urls (short_code, original_url) VALUES (%s, %s) RETURNING *",
            (short_code, body.url)
        )
        row = cur.fetchone()
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail=f"Code '{short_code}' đã tồn tại, thử code khác nhé!")
    finally:
        cur.close()
        conn.close()

    URL_CREATED.inc()
    base = str(request.base_url).rstrip("/")
    return URLResponse(
        short_code=row["short_code"],
        short_url=f"{base}/{row['short_code']}",
        original_url=row["original_url"],
        created_at=str(row["created_at"])
    )

@app.get("/api/stats")
def get_stats():
    """Thống kê tổng quan"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(*) as total_urls, SUM(click_count) as total_clicks FROM urls")
    stats = cur.fetchone()
    cur.execute("SELECT short_code, original_url, click_count, created_at FROM urls ORDER BY click_count DESC LIMIT 10")
    top_urls = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "total_urls": stats["total_urls"],
        "total_clicks": stats["total_clicks"] or 0,
        "top_urls": [dict(u) for u in top_urls]
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    """Health check cho Docker"""
    try:
        conn = get_db()
        conn.close()
        r = get_redis()
        r.ping()
        return {"status": "healthy", "db": "ok", "redis": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/{short_code}")
def redirect_url(short_code: str):
    """Redirect tới URL gốc — route này phải để CUỐI CÙNG"""
    r = get_redis()

    # Check cache trước
    cached = r.get(f"url:{short_code}")
    if cached:
        REDIRECT_COUNT.inc()
        return RedirectResponse(url=cached, status_code=302)

    # Không có cache → query DB
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT original_url FROM urls WHERE short_code = %s", (short_code,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="URL không tồn tại!")

    # Cập nhật click count
    cur.execute("UPDATE urls SET click_count = click_count + 1 WHERE short_code = %s", (short_code,))
    conn.commit()
    cur.close()
    conn.close()

    # Lưu vào cache 1 tiếng
    r.setex(f"url:{short_code}", 3600, row["original_url"])

    REDIRECT_COUNT.inc()
    return RedirectResponse(url=row["original_url"], status_code=302)
