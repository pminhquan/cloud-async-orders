# Archive — README gốc phần SV2 Tuần 1

File này được giữ để truy vết lịch sử tài liệu ban đầu của Khôi.

Thông tin chuẩn hiện tại nên đọc theo thứ tự:

1. [README dự án](../README.md)
2. [Báo cáo Tuần 1](week1-report.md)
3. [Báo cáo Tuần 2](week2-report.md)
4. [Integration Contract](integration-contract.md)
5. [AWS Inventory](aws-inventory.md)

Tóm tắt lịch sử:
- Tuần 1: `order-producer` PoC + `order-api` + `Orders` + SNS; chưa gửi SQS.
- Tuần 2: Producer gửi SQS, có validation; Consumer ghi DynamoDB và idempotency; Full E2E/Retry-DLQ đã được kiểm thử trên Lab Quân.
