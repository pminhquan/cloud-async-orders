# Yêu cầu dự án và ràng buộc kỹ thuật

## 1. Mục tiêu chức năng

Hệ thống cuối cùng cần đáp ứng:

1. `POST /orders` qua API Gateway.
2. Producer Lambda validate request.
3. Request hợp lệ được gửi vào SQS.
4. Request sai trả `400` và không enqueue.
5. Consumer Lambda nhận message SQS.
6. Consumer validate schema và ghi DynamoDB `Orders`.
7. Idempotency theo `orderId`.
8. Message lỗi được retry và chuyển DLQ.
9. Có CloudWatch Logs; cảnh báo CloudWatch Alarm + SNS là mục tiêu giai đoạn sau.
10. Có kịch bản batch/load test và so sánh Standard/FIFO trước khi kết thúc dự án.

## 2. Quy tắc phản hồi Producer

| Tình huống | Kết quả mong đợi |
|---|---|
| Request hợp lệ, gửi SQS thành công | `202 Accepted` |
| Payload sai schema / malformed JSON | `400 Bad Request` |
| Gửi SQS thất bại | `500 Internal Server Error` |

## 3. Schema Tuần 2

```json
{
  "orderId": "UUID",
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2,
  "status": "PENDING",
  "createdAt": "ISO-8601 UTC"
}
```

Chi tiết: [integration-contract.md](integration-contract.md).

## 4. Ràng buộc AWS Learner Lab

- Region: `us-east-1`.
- Lambda dùng `LabRole` có sẵn.
- Không tạo IAM User/Role mới.
- Tổng concurrency Lambda của tài khoản phải nằm trong giới hạn Learner Lab; yêu cầu đề tài đặt mức tối đa 10.
- Tags quy ước:
  - `Project=AsyncOrderProcessing`
  - `Owner=Khoi-Quan`
- Không đưa credential lên GitHub.

## 5. Ràng buộc nhóm

- 2 sinh viên.
- 4 tuần.

## 6. Deliverables

- Source Producer/Consumer.
- Unit tests.
- Script test API/load.
- Tài liệu kỹ thuật trong `docs/`.
- Evidence theo tuần.
- Báo cáo tiến độ và khai báo AI.
- Báo cáo cuối kỳ + video demo ≤ 10 phút.

## 7. Trạng thái theo tuần

### Tuần 1

- PoC SQS/DLQ/Consumer: hoàn thành ở mức độc lập.
- PoC API/Producer/DynamoDB/SNS: hoàn thành ở mức độc lập.
- Full E2E: chưa hoàn thành.

### Tuần 2

- Producer → SQS: hoàn thành.
- Producer validation: hoàn thành.
- Consumer → DynamoDB: hoàn thành.
- Idempotency: hoàn thành.
- Full E2E: PASS trên Lab Quân.
- Retry/DLQ: PASS trên Lab Quân.
- Batch direct invocation: PASS theo kỳ vọng.
- Small load test 10 request: PASS trên Lab Quân.
