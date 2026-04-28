# 🔗 URL Shortener — DevOps Learning Project

> Project học DevOps theo roadmap: Docker → Networking → CI/CD → Monitoring  
> Stack: **Python FastAPI + PostgreSQL + Redis + Nginx + Prometheus + Grafana**  
> Chi phí: **$0/tháng** — chạy hoàn toàn trên máy local

---

## 📁 Cấu trúc project

```
url-shortener/
├── app/
│   ├── main.py              # FastAPI application
│   ├── test_main.py         # Unit tests
│   ├── requirements.txt
│   └── Dockerfile           # Multi-stage build
├── nginx/
│   └── nginx.conf           # Reverse proxy + rate limiting
├── db/
│   └── init.sql             # Schema + sample data
├── prometheus/
│   └── prometheus.yml       # Metrics collection config
├── grafana/
│   └── provisioning/        # Auto-configure datasource
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # GitHub Actions pipeline
├── docker-compose.yml       # Toàn bộ stack
├── .env.example             # Template biến môi trường
└── README.md
```

---

## ✅ Checklist theo Phase

| Phase | Nội dung | Lệnh bắt đầu |
|---|---|---|
| 3 — Docker | Chạy full stack local | `make up` |
| 4 — HTTPS | Bật SSL local | `make ssl-setup` |
| 5 — CI/CD | Push code → tự build | Push lên GitHub |
| 5 — Deploy | Demo live cho HR | `bash scripts/deploy-fly.sh` |
| 6 — Monitoring | Xem dashboard | http://localhost:3000 |

---

## 🚀 Chạy nhanh (Phase 3 — Docker)

### Yêu cầu
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
- Git

### Các bước

```bash
# 1. Clone project
git clone https://github.com/<your-username>/url-shortener.git
cd url-shortener

# 2. Tạo file .env
cp .env.example .env

# 3. Chạy toàn bộ stack
docker compose up -d

# 4. Kiểm tra tất cả đang chạy
docker compose ps

# 5. Xem log
docker compose logs -f app
```

### Truy cập

| Service | URL | Ghi chú |
|---|---|---|
| App (qua Nginx) | http://localhost | Trang chủ |
| API docs | http://localhost/docs | Swagger UI tự động |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Dashboard (admin/admin123) |

---

## 📚 Học theo từng Phase

### Phase 3 — Docker ✅
```bash
# Xem container đang chạy
docker compose ps

# Vào trong container app
docker compose exec app bash

# Xem log realtime
docker compose logs -f app

# Restart 1 service
docker compose restart app

# Xóa hết và chạy lại sạch
docker compose down -v && docker compose up -d
```

**Hiểu được sau phase này:**
- Tại sao cần multi-stage Dockerfile
- Sự khác biệt giữa `networks: backend` và `networks: frontend`
- Tại sao app không expose port 8000 ra ngoài mà phải qua Nginx
- `depends_on` với `healthcheck` giải quyết vấn đề gì

---

### Phase 4 — Networking
Setup HTTPS local bằng `mkcert`:
```bash
# Cài mkcert (Windows: chạy trong PowerShell admin)
winget install mkcert

# Tạo CA và cert cho localhost
mkcert -install
mkcert -cert-file nginx/certs/cert.pem -key-file nginx/certs/key.pem localhost

# Bỏ comment phần HTTPS trong nginx.conf và docker-compose.yml
# Restart nginx
docker compose restart nginx
```

---

### Phase 5 — CI/CD với GitHub Actions

1. Push code lên GitHub
2. Vào **Settings → Secrets and variables → Actions**, thêm:
   - `DOCKERHUB_USERNAME`: username Docker Hub của bạn
   - `DOCKERHUB_TOKEN`: tạo tại hub.docker.com → Account Settings → Security
3. Push bất kỳ thay đổi nào lên `main` → pipeline tự chạy

```bash
git add .
git commit -m "feat: add something"
git push origin main
# → Vào tab Actions trên GitHub để xem pipeline chạy
```

---

### Phase 6 — Monitoring với Grafana

Prometheus + Grafana đã được bật sẵn trong `docker-compose.yml`.

**Tạo dashboard đầu tiên:**
1. Vào http://localhost:3000 (admin / admin123)
2. Chọn **Explore** → chọn datasource **Prometheus**
3. Thử các query:

```promql
# Tổng request theo endpoint
http_requests_total

# Request rate mỗi giây (trung bình 1 phút)
rate(http_requests_total[1m])

# Latency trung bình
rate(http_request_duration_seconds_sum[5m]) 
  / rate(http_request_duration_seconds_count[5m])

# Tổng URL đã tạo
urls_created_total

# Tổng redirect
url_redirects_total
```

---

## 🧪 Chạy tests

```bash
# Chạy tests trong container
docker compose run --rm app pytest -v

# Chạy local (cần có Python + pip install -r requirements.txt)
cd app && pytest -v
```

---

## 🔧 API Reference

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/` | Trang chủ (HTML) |
| `POST` | `/shorten` | Tạo short URL |
| `GET` | `/{code}` | Redirect tới URL gốc |
| `GET` | `/api/stats` | Thống kê |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/docs` | Swagger UI |

**Ví dụ tạo short URL:**
```bash
curl -X POST http://localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com", "custom_code": "gg"}'
```

---

## 💡 Câu hỏi để tự kiểm tra

Sau khi hoàn thành mỗi phase, hãy tự trả lời:

**Phase 3:**
- [ ] Tại sao dùng `python:3.11-slim` thay vì `python:3.11`?
- [ ] Multi-stage build giúp gì cho image size?
- [ ] `docker compose down` vs `docker compose down -v` khác nhau thế nào?
- [ ] Tại sao app cần `depends_on` với `condition: service_healthy`?

**Phase 4:**
- [ ] Nginx đang làm gì mà app không làm trực tiếp được?
- [ ] Rate limiting hoạt động ở tầng nào?
- [ ] Tại sao cần 2 network (frontend/backend) riêng nhau?

**Phase 5:**
- [ ] Pipeline sẽ làm gì khi tests fail?
- [ ] `github.sha` trong image tag có tác dụng gì?
- [ ] Cache trong GitHub Actions giúp gì?

**Phase 6:**
- [ ] `rate()` trong PromQL nghĩa là gì?
- [ ] Tại sao cần Grafana nếu Prometheus đã có UI?
- [ ] Retention 7 ngày trong Prometheus có nghĩa là gì?

---

## 📖 Tài nguyên học thêm

- [FastAPI docs](https://fastapi.tiangolo.com)
- [Docker docs](https://docs.docker.com)
- [Nginx beginner guide](http://nginx.org/en/docs/beginners_guide.html)
- [PromQL cheatsheet](https://promlabs.com/promql-cheat-sheet/)
- [Play with Docker](https://labs.play-with-docker.com) — thực hành online miễn phí
