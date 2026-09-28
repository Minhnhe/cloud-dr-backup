# Cloud Disaster Recovery & Automated Backup

## 1. Mục tiêu

Xây dựng mô hình tự động sao lưu và khôi phục cơ sở dữ liệu MongoDB trên nền tảng Cloud.

## 2. Công nghệ sử dụng

- MongoDB Atlas
- Python
- MongoDB Database Tools
- OpenSSL
- Amazon S3
- GitHub Actions

## 3. Quy trình backup

MongoDB Atlas
→ mongodump
→ gzip
→ AES-256
→ Amazon S3

## 4. Disaster Recovery

Khi xảy ra sự cố, backup được tải từ Amazon S3, giải mã, giải nén và khôi phục vào MongoDB Atlas DR.

## 5. Tự động hóa

GitHub Actions thực hiện backup định kỳ và có thể chạy thủ công thông qua workflow_dispatch.

## 6. Bảo mật

- MongoDB URI được lưu trong GitHub Secrets.
- AWS credentials được lưu trong GitHub Secrets.
- AES encryption key được lưu trong GitHub Secrets.
- File backup và encryption key không được commit lên GitHub.