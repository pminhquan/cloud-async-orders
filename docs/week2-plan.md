# Kế hoạch Tuần 2

## 1. Mục tiêu

Chuyển từ PoC riêng sang hệ thống tích hợp:

```text
API Gateway → Producer → SQS → Consumer → DynamoDB
```

và xác minh:
- input validation;
- idempotency;
- retry/DLQ;
- batch/replay;
- small load test.

## 2. Nhiệm vụ

| Mã | Công việc | Phụ trách | Kết quả |
|---|---|---|---|
| W2-01 | Chốt schema phẳng | Cả hai | Hoàn thành |
| W2-02 | Producer gửi SQS | Khôi | Hoàn thành |
| W2-03 | Producer validation `202/400` | Khôi | Hoàn thành |
| W2-04 | Invalid không enqueue | Khôi | Hoàn thành |
| W2-05 | Consumer ghi DynamoDB | Quân | Hoàn thành |
| W2-06 | Idempotency | Quân | Hoàn thành |
| W2-07 | ORDER_CONFLICT | Quân | Hoàn thành |
| W2-08 | Full E2E | Quân + phối hợp | PASS trên Lab Quân |
| W2-09 | Retry/DLQ | Quân | PASS trên Lab Quân |
| W2-10 | Direct batch/replay | Quân | PASS theo kỳ vọng |
| W2-11 | Small load 10 request | Quân | PASS 10/10 |
| W2-12 | Evidence/report | Cả hai | Đang chốt |
| W2-13 | Worklog ≥ 8h/người | Mỗi người | Nhóm báo cáo đạt tối thiểu 8 giờ; giờ/ngày chi tiết chưa đối soát |

## 3. Cấu hình quan trọng

- Region `us-east-1`.
- `LabRole`.
- `QUEUE_URL` ở Producer.
- `TABLE_NAME=Orders` ở Consumer.
- Queue: `orders-queue`.
- DLQ: `orders-dlq`.
- Redrive test Tuần 2: `maxReceiveCount=5`.
- Concurrency phải không vượt giới hạn 10 của đề tài/Lab.

## 4. Tiêu chí nghiệm thu Tuần 2

- Valid API → `202`.
- Invalid API → `400`.
- Invalid API không enqueue.
- Consumer ghi `PROCESSED`.
- Duplicate cùng payload không tạo duplicate.
- Conflict không overwrite item.
- Invalid JSON retry và đi DLQ.
- Full E2E có cùng `orderId` từ API tới DynamoDB.
- Có tests và evidence.
