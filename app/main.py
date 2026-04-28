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
    <html>
    <head>
        <title>URL Shortener</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 80px auto; padding: 20px; }
            input { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; box-sizing: border-box; }
            button { background: #2563eb; color: white; padding: 10px 24px; border: none; 
                     border-radius: 6px; font-size: 16px; cursor: pointer; }
            button:hover { background: #1d4ed8; }
            #result { margin-top: 20px; padding: 14px; background: #f0fdf4; 
                      border-radius: 8px; display: none; word-break: break-all; }
            .label { font-weight: bold; color: #16a34a; }
        </style>
    </head>
    <body>
        <h1>🔗 URL Shortener</h1>
        <p>DevOps Learning Project — Phase 3</p>
        <input type="text" id="url" placeholder="Nhập URL dài vào đây..." />
        <input type="text" id="code" placeholder="Custom code (tuỳ chọn, vd: my-link)" />
        <button onclick="shorten()">Rút gọn URL</button>
        <div id="result">
            <span class="label">Short URL: </span>
            <a id="short" href="#" target="_blank"></a>
        </div>
        <script>
            async function shorten() {
                const url = document.getElementById('url').value;
                const code = document.getElementById('code').value;
                if (!url) return alert('Nhập URL đi bạn ơi!');
                const body = { url };
                if (code) body.custom_code = code;
                const res = await fetch('/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('short').href = data.short_url;
                    document.getElementById('short').innerText = data.short_url;
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert(data.detail || 'Lỗi rồi!');
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
