# Async Order Processing - Week 1

## Đề tài
Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda.

## Kiến trúc dự kiến
Client → API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB
DLQ → CloudWatch Alarm → SNS → Email

## Mục tiêu Tuần 1
Tuần 1 tập trung làm quen với các dịch vụ AWS, dựng các tài nguyên nền và kiểm thử độc lập từng thành phần. Hệ thống chưa tích hợp hoàn chỉnh với SQS/Consumer trong tuần này.

## Phần triển khai trong Tuần 1
- Tạo DynamoDB table `Orders`
  - Partition key: `orderId`
  - Kiểu: String
  - Capacity mode: On-demand
- Tạo Lambda `order-producer`
  - Runtime: Python
  - Execution role: `LabRole`
  - Memory: 128 MB
  - Timeout: 10 giây
- Xây dựng PoC Producer Lambda để nhận request, sinh `orderId`, tạo dữ liệu đơn hàng ở trạng thái `PENDING` và trả HTTP `202 Accepted`
- Chưa gửi message thật vào SQS trong Tuần 1; phần này sẽ tích hợp ở Tuần 2
- Tạo HTTP API Gateway `order-api`
- Tạo route `POST /orders`
- Kiểm thử API bằng PowerShell và nhận HTTP `202 Accepted`
- Tạo SNS topic `order-dlq-alert`
- Tạo Email Subscription và xác nhận trạng thái `Confirmed`
- Gắn tag:
  - `Project = AsyncOrderProcessing`
  - `Owner = Khoi-Quan`

## Trạng thái tích hợp hiện tại
Các tài nguyên trong thư mục này là phần PoC/kiểm thử Tuần 1. Hai thành viên đang thao tác trên Learner Lab riêng, nên việc thống nhất JSON giữa Producer và Consumer, lựa chọn tài khoản dùng để tích hợp và ghép luồng hoàn chỉnh sẽ thực hiện ở Tuần 2.

## Region
`us-east-1` (N. Virginia)

## API PoC
Route:
```text
POST /orders
```

Body mẫu:
```json
{
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2
}
```

Kết quả kiểm thử hiện tại:
```text
HTTP 202 Accepted
status = PENDING
```

> Lưu ý: HTTP `202` ở Tuần 1 chỉ chứng minh API Gateway và Producer Lambda nhận/xử lý request PoC thành công; chưa chứng minh đơn hàng đã được đưa vào SQS hoặc xử lý bởi Consumer.

## Cấu trúc thư mục
```text
.
├── README.md
├── producer/
│   └── lambda_function.py
├── test-data/
│   └── order-sample.json
├── docs/
│   └── week1.md
└── evidence/
    ├── 01-dynamodb-orders.png
    ├── 02-lambda-producer-202.png
    ├── 03-api-route-post-orders.png
    ├── 04-api-powershell-202.png
    ├── 05-sns-topic.png
    └── 06-sns-email-confirmed.png
```

## Lưu ý bảo mật
Không commit AWS Access Key, Secret Access Key, Session Token, password hoặc file credentials lên repository public.
