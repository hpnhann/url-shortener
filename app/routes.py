import os
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .database import get_db, get_redis
from .schemas import ShortenRequest, URLResponse
from .utils import generate_code
from .metrics import URL_CREATED, REDIRECT_COUNT

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home():
    """Trang chủ đơn giản"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@router.post("/shorten", response_model=URLResponse)
def shorten_url(body: ShortenRequest, request: Request):
    """Tạo short URL mới"""
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

@router.get("/api/stats")
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

@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/health")
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

@router.get("/{short_code}")
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
