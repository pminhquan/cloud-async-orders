# Phân công nhiệm vụ

## 1. Thành viên

| MSSV | Họ tên | Vai trò chính |
|---|---|---|
| 24110311 | Phạm Minh Quân | SQS/DLQ, Consumer, DynamoDB/idempotency, retry/DLQ, batch/load, kiến trúc |
| 24110259 | Nguyễn Đoàn Minh Khôi | API Gateway, Producer, validation, SNS, evidence/report, phối hợp integration contract |

---

## 2. Phân công Tuần 1

### Phạm Minh Quân

- Nghiên cứu SQS Standard/FIFO và DLQ.
- Tạo `orders-queue` và `orders-dlq`.
- Cấu hình redrive.
- Tạo Consumer Lambda PoC.
- Test valid message.
- Test invalid message.
- Test retry và DLQ.
- Thu thập evidence SQS/Lambda/DLQ.
- Vẽ sơ đồ kiến trúc.

### Nguyễn Đoàn Minh Khôi

- Nghiên cứu API Gateway, Lambda, DynamoDB, SNS.
- Tạo DynamoDB `Orders`.
- Tạo `order-producer` PoC.
- Tạo `order-api` và `POST /orders`.
- Test API trả `202`.
- Tạo SNS `order-dlq-alert`.
- Xác nhận email subscription.
- Thu thập evidence API/Producer/DynamoDB/SNS.

### Kết quả chung Tuần 1

Hai phía được test riêng. Full E2E chưa được coi là hoàn thành.

---

## 3. Phân công Tuần 2

### Phạm Minh Quân

- Nâng cấp `order-consumer` theo schema phẳng.
- Kết nối DynamoDB `Orders`.
- Conditional write `attribute_not_exists(orderId)`.
- Idempotency replay.
- `ORDER_CONFLICT`.
- Unit tests Consumer.
- Full E2E trên Lab Quân.
- Invalid JSON → Retry → DLQ.
- Direct batch valid/mixed/replay.
- Small load test 10 request.
- Bộ evidence AWS Tuần 2 phía Quân.

### Nguyễn Đoàn Minh Khôi

- Nâng cấp `order-producer` gửi SQS thật.
- Cấu hình `QUEUE_URL`.
- Producer input validation.
- Valid → `202`.
- Invalid → `400`.
- Xác nhận invalid request không enqueue.
- Phối hợp kiểm tra queue backlog/DLQ.
- Bộ evidence Producer/SQS Tuần 2 phía Khôi.
- Tổng hợp tài liệu và khai báo AI theo thông tin thực tế từng người cung cấp.

### Phần thực hiện chung

- Chốt Integration Contract.
- Chốt schema.
- Phối hợp E2E.
- Review PR.
- Kiểm tra source/tests/evidence trước khi nộp.

---

## 4. Quy tắc tránh làm trùng

Hai AWS Learner Lab có thể độc lập. Không bắt buộc cả hai phải dựng lại toàn bộ hệ thống nếu nhóm đã chọn một Lab làm môi trường integration chính và có evidence rõ ràng.

Mỗi thành viên vẫn phải có:
- phần code/tài liệu/evidence của chính mình;
- worklog thực tế;
- khả năng giải thích toàn bộ luồng khi demo.

---

## 5. Worklog

- Tuần 1: [worklog/week1.md](worklog/week1.md)
- Tuần 2: [worklog/week2.md](worklog/week2.md)

Mỗi người tối thiểu 8 giờ thực tế/tuần.
