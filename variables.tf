# ── variables.tf — Khai báo các biến ────────────────────────
# Giống như function parameters — tái sử dụng cho nhiều môi trường
# dev, staging, production chỉ cần đổi giá trị biến

variable "aws_region" {
  description = "AWS region để deploy"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Tên project — dùng để đặt tên tất cả resources"
  type        = string
  default     = "url-shortener"
}

variable "environment" {
  description = "Môi trường: dev, staging, production"
  type        = string
  default     = "dev"

  # Validation: chỉ cho phép 3 giá trị này
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment phải là: dev, staging, hoặc production."
  }
}

variable "app_version" {
  description = "Version của Docker image"
  type        = string
  default     = "latest"
}

# ── Local values: tính toán từ variables ────────────────────
# Giống như biến derived — không cần người dùng nhập
locals {
  # Prefix cho tất cả resource names
  prefix = "${var.project_name}-${var.environment}"

  # Tags chung cho tất cả resources — best practice AWS
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"    # biết resource này do Terraform tạo
    Owner       = "phucnhan"
  }
}
