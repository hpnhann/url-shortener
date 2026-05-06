# 🚀 Hướng Dẫn Chạy Terraform + LocalStack (Local AWS)

File `main.tf` của bạn được cấu hình để dùng **LocalStack** (một công cụ giả lập AWS ngay trên máy tính của bạn thông qua Docker, chạy ở cổng `4566`). Nhờ đó, bạn có thể thực hành tạo hạ tầng AWS (S3, VPC,...) hoàn toàn miễn phí ($0) trước khi đẩy lên AWS thật.

Dưới đây là từng bước để khởi chạy và tạo tài nguyên:

## Bước 1: Khởi động LocalStack
Vì Terraform cần nói chuyện với AWS, chúng ta phải bật giả lập LocalStack lên trước. Mở terminal và chạy lệnh:
```bash
docker run --rm -d --name localstack -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack:3.8.0
```

## Bước 2: Khởi tạo Terraform (`init`)
Tải các plugin và thư viện (providers) cần thiết (ở đây là `hashicorp/aws` như khai báo trong `main.tf`).
```bash
terraform init
```

## Bước 3: Xem trước các thay đổi (`plan`)
Lệnh này giúp bạn xem Terraform "dự định" sẽ tạo ra những gì (ví dụ: tạo 3 S3 buckets trong `storage.tf` và VPC trong `networking.tf`), mà chưa áp dụng thực tế. 
Sử dụng giá trị biến từ file `dev.tfvars`.
```bash
terraform plan -var-file="dev.tfvars"
```

## Bước 4: Áp dụng tạo hạ tầng (`apply`)
Nếu plan đưa ra kết quả đúng đắn, hãy ra lệnh cho Terraform thực sự tạo các tài nguyên đó trên LocalStack:
```bash
terraform apply -var-file="dev.tfvars"
```
*Bạn sẽ cần gõ `yes` khi được hỏi để xác nhận.*
*(Muốn chạy nhanh mà không cần gõ yes, bạn có thể thêm cờ `-auto-approve`: `terraform apply -var-file="dev.tfvars" -auto-approve`)*

## Bước 5: Kiểm tra thành quả
Sau khi apply thành công, bạn có thể kiểm tra xem S3 buckets đã thực sự được tạo trong LocalStack hay chưa bằng AWS CLI:
```bash
docker exec localstack awslocal s3 ls
```

## Bước 6: Dọn dẹp (`destroy`)
Khi học xong, bạn có thể dọn dẹp (xóa toàn bộ những resource đã tạo) để trả lại trạng thái sạch sẽ:
```bash
terraform destroy -var-file="dev.tfvars"
```
*(Gõ `yes` để xác nhận xóa)*

Sau đó tắt và xóa container LocalStack:
```bash
docker stop localstack
```
