# Phân công nhiệm vụ

## 1. Thành viên

| MSSV | Họ tên | Vai trò chính |
|---|---|---|
| 24110311 | Phạm Minh Quân | SQS/DLQ, Consumer, DynamoDB/idempotency, retry/DLQ, batch/load, CloudWatch monitoring/metrics, SQS Standard vs FIFO benchmark, kiến trúc |
| 24110259 | Nguyễn Đoàn Minh Khôi | API Gateway, Producer, validation, SNS topic/email subscription & xác minh cảnh báo, evidence/report, phối hợp integration contract |

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

### Phần thực hiện chung Tuần 2

- Chốt Integration Contract.
- Chốt schema.
- Phối hợp E2E.
- Review PR.
- Kiểm tra source/tests/evidence trước khi nộp.

---

## 4. Phân công Tuần 3

### Phạm Minh Quân

- Thiết kế và triển khai CloudWatch Monitoring & DLQ Alarm (`iac/week3-monitoring.yaml`).
- Xây dựng và thực thi công cụ benchmark SQS Standard vs FIFO (`scripts/benchmark_sqs.py`) trên các queue thử nghiệm độc lập.
- Xây dựng công cụ controlled load test và đối soát DynamoDB `GetItem` theo `orderId` (`scripts/load_test_orders.py`).
- Xây dựng công cụ thu thập CloudWatch metrics (`scripts/collect_cloudwatch_metrics.py`) và tổng hợp báo cáo hiệu năng (`scripts/generate_week3_report.py`).
- Viết automated unit tests cho toàn bộ công cụ Tuần 3 và thiết lập GitHub Actions CI (`.github/workflows/python-tests.yml`).
- Thực hiện kiểm chứng trên AWS Learner Lab theo `docs/week3-aws-manual-runbook.md`, thu thập technical evidence và cập nhật báo cáo kỹ thuật.

### Nguyễn Đoàn Minh Khôi

- Quản lý và đối soát cấu hình SNS Topic `order-dlq-alert` cùng trạng thái xác nhận (`Confirmed`) của email subscription.
- Phối hợp kiểm tra tính tương thích của `order-api` (`POST /orders`) và `order-producer` khi thực hiện controlled load test.
- Xác minh nhận thông báo email cảnh báo end-to-end khi `DLQVisibleMessagesAlarm` chuyển sang `ALARM`.
- Rà soát bộ tài liệu Tuần 3, cung cấp ảnh minh chứng phần SNS/email và tổng hợp phần công việc phụ trách.

---

## 5. Quy tắc tránh làm trùng và bảo đảm trung thực

Hai AWS Learner Lab có thể độc lập. Không bắt buộc cả hai phải dựng lại toàn bộ hệ thống nếu nhóm đã chọn một Lab làm môi trường integration chính và có evidence rõ ràng. Không gán công việc đã thực hiện của Quân cho Khôi hoặc ngược lại; kết quả ghi vào tài liệu phải dựa trên bằng chứng thực tế và đúng người thực hiện.

Mỗi thành viên vẫn phải có:
- phần code/tài liệu/evidence của chính mình;
- danh mục công việc và minh chứng;
- khả năng giải thích toàn bộ luồng khi demo.

---

## 6. Danh mục công việc

- Tuần 1: [worklog/week1.md](worklog/week1.md)
- Tuần 2: [worklog/week2.md](worklog/week2.md)
