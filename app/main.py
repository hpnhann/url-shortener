import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .metrics import REQUEST_COUNT, REQUEST_LATENCY
from .routes import router

# ── App setup ──────────────────────────────────────────────
app = FastAPI(
    title="URL Shortener",
    description="A DevOps learning project — Modularized",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ── Include Routes ──────────────────────────────────────────
app.include_router(router)
