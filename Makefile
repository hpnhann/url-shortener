# ── Makefile — Gõ lệnh ngắn thay vì nhớ docker compose dài ──
# Dùng: make <lệnh>
# Ví dụ: make up, make logs, make test

.PHONY: help up down restart logs test build clean ssl-setup ps shell-app shell-db

# ── Mặc định: hiện help ──────────────────────────────────────
help:
	@echo ""
	@echo "  🐳 URL Shortener — Các lệnh có sẵn"
	@echo "  ─────────────────────────────────────────────"
	@echo "  make up          Khởi động toàn bộ stack"
	@echo "  make down        Dừng stack"
	@echo "  make restart     Restart toàn bộ"
	@echo "  make ps          Xem trạng thái containers"
	@echo "  make logs        Xem log realtime (tất cả)"
	@echo "  make logs-app    Xem log của app"
	@echo "  make test        Chạy unit tests"
	@echo "  make build       Build lại image"
	@echo "  make clean       Xóa tất cả (kể cả data!)"
	@echo "  make ssl-setup   Bật HTTPS local (cần mkcert)"
	@echo "  make shell-app   Vào terminal của app container"
	@echo "  make shell-db    Vào PostgreSQL console"
	@echo "  make stats       Xem thống kê API"
	@echo "  make open        Mở app trong trình duyệt"
	@echo ""

# ── Phase 3: Docker cơ bản ───────────────────────────────────
up:
	@echo "🚀 Starting URL Shortener stack..."
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d
	@echo ""
	@echo "✅ Stack is up!"
	@echo "   App:        http://localhost"
	@echo "   API docs:   http://localhost/docs"
	@echo "   Grafana:    http://localhost:3000  (admin/admin123)"
	@echo "   Prometheus: http://localhost:9090"

down:
	docker compose down

restart:
	docker compose restart

ps:
	docker compose ps

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f app

build:
	docker compose build --no-cache app
	docker compose up -d app

# Xóa hết kể cả volumes (DATA SẼ MẤT!)
clean:
	@echo "⚠️  Xóa toàn bộ containers và data..."
	docker compose down -v --remove-orphans
	@echo "✅ Cleaned!"

# ── Phase 4: HTTPS setup ─────────────────────────────────────
ssl-setup:
	bash scripts/setup-ssl.sh

ssl-off:
	@echo "🔄 Switching back to HTTP..."
	cp nginx/nginx-http.conf.bak nginx/nginx.conf
	docker compose restart nginx
	@echo "✅ Back to HTTP: http://localhost"

# ── Phase 5: CI/CD ───────────────────────────────────────────
# Simulate CI locally trước khi push
ci-local:
	@echo "🧪 Running CI pipeline locally..."
	@make test
	@make build
	@echo "✅ Local CI passed! Safe to push."

# ── Phase 6: Monitoring ──────────────────────────────────────
stats:
	@curl -s http://localhost/api/stats | python3 -m json.tool

# ── Dev helpers ──────────────────────────────────────────────
test:
	@echo "🧪 Running tests..."
	docker compose run --rm app pytest -v --tb=short
	@echo "✅ Tests passed!"

shell-app:
	docker compose exec app bash

shell-db:
	docker compose exec db psql -U postgres -d urlshortener

# Tạo thử 10 URL để có data trong Grafana
seed:
	@echo "🌱 Seeding test data..."
	@for url in https://google.com https://github.com https://youtube.com \
	             https://facebook.com https://twitter.com https://reddit.com \
	             https://stackoverflow.com https://netflix.com https://amazon.com \
	             https://wikipedia.org; do \
	    curl -s -X POST http://localhost/shorten \
	        -H "Content-Type: application/json" \
	        -d "{\"url\": \"$$url\"}" > /dev/null; \
	done
	@echo "✅ 10 URLs created! Check http://localhost/api/stats"

open:
	@echo "Opening app..."
	@python3 -c "import webbrowser; webbrowser.open('http://localhost')" 2>/dev/null || \
	 xdg-open http://localhost 2>/dev/null || \
	 start http://localhost 2>/dev/null || \
	 echo "Mở trình duyệt và vào: http://localhost"
