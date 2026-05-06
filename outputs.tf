# ── outputs.tf — In ra thông tin sau khi apply ──────────────
# Giống như return value của function
# Dùng để biết địa chỉ server, tên bucket, v.v.

output "s3_assets_bucket" {
  description = "Tên S3 bucket lưu static assets"
  value       = aws_s3_bucket.app_assets.bucket
}

output "s3_backups_bucket" {
  description = "Tên S3 bucket lưu DB backups"
  value       = aws_s3_bucket.db_backups.bucket
}

output "s3_state_bucket" {
  description = "Tên S3 bucket lưu Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "vpc_id" {
  description = "ID của VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID của public subnet (cho Nginx)"
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "ID của private subnet (cho App + DB)"
  value       = aws_subnet.private.id
}

output "nginx_security_group_id" {
  description = "Security Group ID cho Nginx"
  value       = aws_security_group.nginx.id
}

output "app_security_group_id" {
  description = "Security Group ID cho App"
  value       = aws_security_group.app.id
}

output "db_security_group_id" {
  description = "Security Group ID cho DB"
  value       = aws_security_group.db.id
}

output "environment_summary" {
  description = "Tóm tắt môi trường đã tạo"
  value = {
    project     = var.project_name
    environment = var.environment
    region      = var.aws_region
    prefix      = local.prefix
  }
}
