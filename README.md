# 🔗 URL Shortener — DevOps Learning Project

> Project học DevOps theo roadmap: Docker → Networking → Cấu trúc Code → Terraform (IaC) → CI/CD → Monitoring  
> Stack: **Python FastAPI + PostgreSQL + Redis + Nginx + Prometheus + Grafana + Terraform (LocalStack)**  
> Chi phí: **$0/tháng** — chạy hoàn toàn trên máy local

---

## 📁 Cấu trúc project hiện tại (Đã Refactor)

```text
url-shortener/
├── app/                     # FastAPI application (Đã được module hoá)
│   ├── main.py              # Entry point, setup Middleware & Router
│   ├── database.py          # Kết nối PostgreSQL & Redis, init DB
│   ├── routes.py            # Chứa các API endpoints
│   ├── schemas.py           # Pydantic models (Input/Output)
│   ├── utils.py             # Hàm tiện ích (random code)
│   ├── metrics.py           # Định nghĩa Prometheus metrics
│   ├── templates/           # Thư mục chứa giao diện web
│   │   └── index.html       # Giao diện UI Premium
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
├── docker-compose.yml       # Toàn bộ stack (Nginx chạy port 8080)
├── TERRAFORM_GUIDE.md       # Hướng dẫn chi tiết chạy Terraform
├── main.tf, storage.tf, networking.tf, compute.tf # Code hạ tầng Terraform
├── dev.tfvars, staging.tfvars # Biến môi trường cho Terraform
├── .env.example             # Template biến môi trường
└── README.md
```

---

## ✅ Checklist theo Phase

| Phase | Nội dung | Lệnh bắt đầu |
|---|---|---|
| 3 — Docker | Chạy full stack local (App, DB, Redis, Nginx) | `docker compose up -d` |
| 4 — Code Structure | Refactor từ 1 file `main.py` khổng lồ sang kiến trúc module gọn gàng | |
| 5 — IaC (Terraform) | Xây dựng hạ tầng Cloud giả lập với LocalStack (VPC, EC2, S3, Security Groups) | `terraform apply -var-file="dev.tfvars"` |
| 6 — CI/CD | Push code → tự build | Push lên GitHub |
| 7 — Monitoring | Xem dashboard đo đạc hiệu năng | http://localhost:3000 |

---

## 🚀 Chạy nhanh App (Phase 3 & 4 — Docker & App)

### Yêu cầu
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
- Git

### Các bước chạy

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
```

### Truy cập

| Service | URL | Ghi chú |
|---|---|---|
| App (qua Nginx) | **http://localhost:8080** | Trang chủ URL Shortener (đã đổi sang 8080 để tránh xung đột WSL/Windows IIS) |
| API docs | http://localhost:8080/docs | Swagger UI tự động |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Dashboard (admin/admin123) |

---

## ☁️ Terraform & LocalStack (Phase 5 — Infrastructure as Code)

Mục tiêu của phase này là tự động hóa việc tạo mạng (VPC), máy chủ (EC2), và nơi lưu trữ (S3) thông qua code thay vì bấm tay trên giao diện AWS.

**Kiến trúc 3-Tier Security:**
- **Public Subnet:** Chứa Nginx EC2 (Có Internet Gateway để đón khách từ ngoài vào).
- **Private Subnet:** Chứa App EC2 & Database (Cách ly hoàn toàn khỏi Internet).
- **Security Groups:** 
  - Nginx mở port 80/443 ra ngoài.
  - App mở port 8000 nhưng **chỉ nhận** traffic từ Nginx.
  - DB mở port 5432 nhưng **chỉ nhận** traffic từ App.

**Cách chạy Terraform (Xem kỹ trong `TERRAFORM_GUIDE.md`):**
```bash
# 1. Bật LocalStack lên trước
docker run --rm -it -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack:3.8.0

# 2. Ở terminal khác, chạy Terraform
terraform init -upgrade
terraform plan -var-file="dev.tfvars"
terraform apply -var-file="dev.tfvars" -auto-approve

# 3. Triển khai môi trường staging (Độc lập hoàn toàn với dev)
terraform apply -var-file="staging.tfvars" -auto-approve
```

> **Bài học quan trọng trong quá trình làm:**
> - AWS API yêu cầu tham chiếu `subnet_id` bằng chuỗi ID (`subnet-xxx`) do AWS cấp phát chứ không phải dải CIDR (`10.0.1.0/24`).
> - EC2 nằm trong VPC bắt buộc phải dùng `vpc_security_group_ids` thay vì `security_groups`.

---

## 🤖 Ansible (Configuration Management & Automation)

Ansible đóng vai trò như một **Đạo diễn**, giúp tự động hoá việc cấu hình hàng loạt máy chủ mà không cần cài đặt agent (Agentless) và đảm bảo tính nhất quán (Idempotent).

Trong project này, chúng ta có các Playbook (`ansible/`):
- `backup.yml`: Tự động kết nối, chạy `pg_dump` backup database và lưu vào `/tmp/backups/`.
- `health-check.yml`: Kiểm tra dung lượng đĩa cứng, tự động phát cảnh báo đỏ (fail) nếu đĩa đầy > 80%.
- `local-test.yml`: Playbook test chạy trực tiếp trên máy local (`connection: local`) để kiểm tra Docker, cấu hình hệ thống, và gọi thẳng các health-check task.

**Chạy thử Ansible Playbook (trên Windows PowerShell):**
Vì Ansible không chạy trực tiếp được trên Windows, bạn cần thêm chữ `wsl` ở đầu lệnh để chạy thông qua môi trường Linux (Ubuntu) đã cài trong máy:

```powershell
# Chạy script backup database
wsl ansible-playbook ansible/backup.yml

# Chạy test local & kiểm tra health check
wsl ansible-playbook ansible/local-test.yml
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

**Ví dụ tạo short URL:**
```bash
curl -X POST http://localhost:8080/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com", "custom_code": "gg"}'
```

---

## 💡 Câu hỏi để tự kiểm tra

Sau khi hoàn thành mỗi phase, hãy tự trả lời:

**Phase Docker & Cấu trúc Code:**
- [ ] Tại sao app cần `depends_on` với `condition: service_healthy` đối với database?
- [ ] Việc tách `main.py` thành `routes.py`, `database.py` có lợi ích gì khi làm việc nhóm?
- [ ] Tại sao Nginx port 80 trên Windows hay bị xung đột (Ví dụ: với WSL wslrelay.exe)?

**Phase Terraform:**
- [ ] `outputs.tf` đóng vai trò gì giống với khái niệm nào trong lập trình?
- [ ] Tại sao Database lại đặt trong Private Subnet mà không đặt chung với Nginx ở Public Subnet?
- [ ] Việc dùng file `dev.tfvars` và `staging.tfvars` giải quyết bài toán gì khi quản lý hạ tầng?
