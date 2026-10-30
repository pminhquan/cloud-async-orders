# Phần Nguyễn Đoàn Minh Khôi — Tuần 1

Tài liệu này giữ lại để truy vết phần việc cá nhân của Khôi trong Tuần 1. Báo cáo nhóm đầy đủ xem [week1-report.md](week1-report.md).

## Công việc

- Nghiên cứu API Gateway, Lambda, DynamoDB, SNS.
- Tạo DynamoDB `Orders`, partition key `orderId`, On-demand.
- Tạo `order-producer` PoC.
- Tạo HTTP API `order-api`.
- Route `POST /orders`.
- Test Lambda/API trả `202`.
- Tạo SNS `order-dlq-alert`.
- Email subscription `Confirmed`.

## Giới hạn Tuần 1

Producer chỉ tạo order `PENDING` và trả `202`; **chưa gửi SQS thật**. Producer → SQS và Consumer → DynamoDB thuộc Tuần 2.

## Evidence

```text
docs/evidence/week1/sv2/
```

- `01-dynamodb-orders.png`
- `02-lambda-producer-202.png`
- `03-api-route-post-orders.png`
- `04-api-powershell-202.png`
- `05-sns-topic.png`
- `06-sns-email-confirmed.png`
