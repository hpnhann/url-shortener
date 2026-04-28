#!/bin/bash
# ── setup-ssl.sh — Tự động setup HTTPS local ────────────────
# Chạy: bash scripts/setup-ssl.sh
# Yêu cầu: mkcert đã được cài

set -e

CERT_DIR="./nginx/certs"

echo "🔐 Setting up local HTTPS with mkcert..."

# Kiểm tra mkcert đã cài chưa
if ! command -v mkcert &> /dev/null; then
    echo ""
    echo "❌ mkcert chưa được cài. Cài theo hướng dẫn:"
    echo ""
    echo "  Windows (PowerShell Admin):"
    echo "    winget install mkcert"
    echo ""
    echo "  macOS:"
    echo "    brew install mkcert"
    echo ""
    echo "  Linux (Ubuntu):"
    echo "    sudo apt install libnss3-tools"
    echo "    curl -L https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-linux-amd64 -o mkcert"
    echo "    chmod +x mkcert && sudo mv mkcert /usr/local/bin/"
    echo ""
    exit 1
fi

# Tạo thư mục certs
mkdir -p "$CERT_DIR"

# Cài local CA vào hệ thống (chỉ cần 1 lần)
echo "📜 Installing local CA..."
mkcert -install

# Tạo cert cho localhost
echo "📋 Generating certificate for localhost..."
mkcert \
    -cert-file "$CERT_DIR/cert.pem" \
    -key-file  "$CERT_DIR/key.pem" \
    localhost 127.0.0.1 ::1

echo ""
echo "✅ SSL certificates created:"
echo "   $CERT_DIR/cert.pem"
echo "   $CERT_DIR/key.pem"
echo ""
echo "🔄 Switching Nginx to HTTPS config..."

# Backup config hiện tại và dùng SSL config
cp ./nginx/nginx.conf    ./nginx/nginx-http.conf.bak
cp ./nginx/nginx-ssl.conf ./nginx/nginx.conf

echo ""
echo "🚀 Restarting Nginx with HTTPS..."
docker compose restart nginx

echo ""
echo "✅ Done! Truy cập: https://localhost"
echo "   (Chrome có thể cảnh báo lần đầu — bấm Advanced → Proceed)"
