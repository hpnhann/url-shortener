# ── main.tf — Terraform entry point ─────────────────────────
# Terraform = "viết code để tạo hạ tầng"
# File này khai báo: dùng provider nào, version bao nhiêu

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── Provider: kết nối tới LocalStack (giả lập AWS) ──────────
# Khi deploy thật lên AWS, chỉ cần đổi endpoint và credentials
provider "aws" {
  region = var.aws_region

  # LocalStack config — xóa block này khi dùng AWS thật
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3             = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    iam            = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    cloudwatchlogs = "http://localhost:4566"
  }

  # S3 path style (cần cho LocalStack)
  s3_use_path_style = true
}
