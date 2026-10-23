# Kế hoạch và phạm vi Tuần 1

## 1. Mục tiêu

Tuần 1 dùng để:
- nghiên cứu dịch vụ;
- thiết kế kiến trúc;
- dựng nền AWS;
- kiểm thử PoC riêng hai phía;
- thu thập evidence ban đầu.

Không đặt mục tiêu Full E2E trong Tuần 1.

## 2. Kế hoạch

| Mã | Công việc | Người phụ trách | Kết quả Tuần 1 |
|---|---|---|---|
| W1-01 | Nghiên cứu SQS Standard/FIFO, DLQ | Quân | Hoàn thành |
| W1-02 | Nghiên cứu API Gateway, Lambda, DynamoDB, SNS | Khôi | Hoàn thành |
| W1-03 | Sơ đồ kiến trúc | Quân + Khôi góp ý | Hoàn thành |
| W1-04 | Tạo SQS/DLQ/Consumer PoC | Quân | Hoàn thành |
| W1-05 | Test valid/invalid/retry/DLQ PoC | Quân | Hoàn thành |
| W1-06 | Tạo DynamoDB/Producer/API PoC | Khôi | Hoàn thành |
| W1-07 | Test `POST /orders` → `202` | Khôi | Hoàn thành |
| W1-08 | Tạo SNS topic/email | Khôi | Hoàn thành |
| W1-09 | Chuẩn hóa repository/evidence | Cả hai | Hoàn thành |

## 3. Tiêu chí hoàn thành Tuần 1

- Có source Producer PoC và Consumer PoC.
- Có SQS/DLQ.
- Có API Gateway/DynamoDB/SNS.
- Có evidence AWS.
- Có kiến trúc và Integration Contract dự thảo.
- Không tuyên bố Full E2E nếu Producer chưa gửi SQS và Consumer chưa ghi DynamoDB.

## 4. Chuyển tiếp sang Tuần 2

Tuần 2 thực hiện:
- Producer → SQS thật.
- Schema chung.
- Consumer → DynamoDB.
- Idempotency.
- Full E2E.
- Retry/DLQ tích hợp.
- Batch/load test nhỏ.
