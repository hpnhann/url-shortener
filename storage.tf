# ── storage.tf — S3 buckets ──────────────────────────────────
# S3 = Simple Storage Service
# Dùng để lưu: static files, backups, logs, Docker images

# ── Bucket 1: Lưu static assets của app ─────────────────────
resource "aws_s3_bucket" "app_assets" {
  # Tên bucket phải unique toàn cầu trên AWS
  bucket = "${local.prefix}-assets"
  tags   = local.common_tags
}

# Bật versioning — giữ lại lịch sử file, rollback được
resource "aws_s3_bucket_versioning" "app_assets" {
  bucket = aws_s3_bucket.app_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access — best practice bảo mật
resource "aws_s3_bucket_public_access_block" "app_assets" {
  bucket = aws_s3_bucket.app_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Bucket 2: Lưu DB backups ────────────────────────────────
resource "aws_s3_bucket" "db_backups" {
  bucket = "${local.prefix}-db-backups"
  tags   = local.common_tags
}



# ── Bucket 3: Lưu Terraform state ───────────────────────────
# Quan trọng! State file ghi lại "hiện tại hạ tầng đang như thế nào"
# Lưu trên S3 để team share được, không mất khi máy hỏng
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${local.prefix}-terraform-state"
  tags   = merge(local.common_tags, { Purpose = "terraform-state" })
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"   # PHẢI bật — để rollback state khi cần
  }
}

# Upload file cấu hình app lên S3 (ví dụ minh họa)
resource "aws_s3_object" "app_config" {
  bucket  = aws_s3_bucket.app_assets.id
  key     = "config/app-config.json"
  content = jsonencode({
    project     = var.project_name
    environment = var.environment
    version     = var.app_version
    created_at  = timestamp()
  })
  content_type = "application/json"
  tags         = local.common_tags
}
