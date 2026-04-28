#!/bin/bash
# ── deploy.sh — Deploy lên Fly.io (miễn phí) ────────────────
# Dùng khi muốn demo live cho nhà tuyển dụng
# Fly.io free tier: 3 shared VMs + 3GB storage

set -e

APP_NAME="url-shortener-$(whoami)"   # tên unique

echo "🚀 Deploying to Fly.io (free tier)..."
echo ""

# Kiểm tra flyctl đã cài chưa
if ! command -v flyctl &> /dev/null; then
    echo "📦 Cài flyctl..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Đăng nhập (sẽ mở browser)
echo "🔐 Login to Fly.io..."
flyctl auth login

# Tạo app nếu chưa có
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "📋 Creating app: $APP_NAME"
    flyctl apps create "$APP_NAME"
fi

# Tạo PostgreSQL database (free tier)
echo "🗄️  Setting up PostgreSQL..."
flyctl postgres create \
    --name "$APP_NAME-db" \
    --region sin \
    --initial-cluster-size 1 \
    --vm-size shared-cpu-1x \
    --volume-size 1 || echo "DB already exists"

# Attach DB vào app
flyctl postgres attach "$APP_NAME-db" --app "$APP_NAME" || echo "Already attached"

# Set Redis (dùng Upstash - free tier 10k requests/day)
echo ""
echo "⚡ Upstash Redis setup:"
echo "   1. Vào https://upstash.com → tạo Redis DB miễn phí"
echo "   2. Copy REDIS_URL"
echo "   3. Chạy: flyctl secrets set REDIS_HOST=<your-upstash-host> --app $APP_NAME"
echo ""

# Deploy
echo "🐳 Deploying Docker image..."
flyctl deploy \
    --app "$APP_NAME" \
    --dockerfile app/Dockerfile \
    --remote-only

echo ""
echo "✅ Deployed successfully!"
echo "   URL: https://$APP_NAME.fly.dev"
echo ""
echo "📊 Monitor:"
echo "   flyctl logs --app $APP_NAME"
echo "   flyctl status --app $APP_NAME"
