# ── Stage 1: Builder ────────────────────────────────────────
# Cài dependencies riêng để tận dụng Docker layer cache
FROM python:3.11-slim AS builder

WORKDIR /install

COPY requirements.txt .

# Cài vào thư mục riêng để copy sang stage sau
RUN pip install --prefix=/install/deps --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ────────────────────────────────────────
# Image nhỏ hơn, không có build tools
FROM python:3.11-slim

# Tạo user không phải root — best practice bảo mật
RUN useradd --create-home appuser

WORKDIR /app

# Copy dependencies từ builder stage
COPY --from=builder /install/deps /usr/local

# Copy source code
COPY . .

# Đổi owner sang appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check — Docker tự restart nếu app lỗi
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
