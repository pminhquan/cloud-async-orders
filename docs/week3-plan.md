# Kế hoạch Tuần 3 — Observability, SQS Standard vs FIFO Benchmark & Controlled Load Test

## 1. Mục tiêu

Hoàn thiện tầng giám sát/cảnh báo (CloudWatch Alarm → SNS), công cụ benchmark độc lập so sánh SQS Standard và SQS FIFO, công cụ kiểm thử tải có kiểm soát kèm đối soát DynamoDB `GetItem`, bộ thu thập CloudWatch metrics, GitHub Actions CI và tài liệu hướng dẫn nghiệm thu cho Tuần 3.

Giữ nguyên hợp đồng tích hợp (`docs/integration-contract.md`) và toàn bộ 33 unit tests regression của Producer/Consumer đã hoàn thành ở Tuần 2.

---

## 2. Phạm vi triển khai (W3-01 → W3-07)

| Mã | Hạng mục | Nội dung chính | Phụ trách chính |
|---|---|---|---|
| **W3-01** | CloudWatch Monitoring & SNS Alert | Template IaC `iac/week3-monitoring.yaml` (tham chiếu SNS ARN hiện có `order-dlq-alert`, không tạo IAM Role mới), script `scripts/collect_cloudwatch_metrics.py`, unit tests và tài liệu giám sát. | Quân (IaC, metric collector, DLQ alarm); Khôi (SNS topic/email subscription & xác minh email E2E) |
| **W3-02** | SQS Standard vs FIFO Benchmark | Công cụ `scripts/benchmark_sqs.py` hỗ trợ Standard, FIFO (`single-group` và `multi-group`), đo throughput/latency/duplicate/ordering trên queue thử nghiệm riêng. | Quân |
| **W3-03** | Controlled Load Test & E2E Verification | Công cụ `scripts/load_test_orders.py` kiểm thử `POST /orders` trong giới hạn concurrency `<= 10`, phân biệt `HTTP 202` với `DynamoDB PROCESSED` qua `GetItem` có backoff/timeout. | Quân; Khôi phối hợp kiểm tra tương thích API/Producer |
| **W3-04** | Metrics Collector & Performance Report | Chuẩn hóa thu thập CloudWatch metrics (UTC, giữ `null` khi `NO_DATA`) và công cụ `scripts/generate_week3_report.py` tổng hợp JSON sang Markdown có phân tách nguồn dữ liệu; CSV dùng để đối chiếu. | Quân |
| **W3-05** | Test Automation & Regression | Mở rộng bộ test offline (`tests/test_monitoring_and_metrics.py`, `tests/test_benchmark_sqs.py`, `tests/test_load_test_orders.py`), bảo toàn 33 test methods cũ. | Quân |
| **W3-06** | GitHub Actions CI | Workflow `.github/workflows/python-tests.yml` tự động chạy `cfn-lint iac/week3-monitoring.yaml`, compileall, pytest, unittest và kiểm tra CLI dry-run với quyền tối thiểu (`contents: read`), không dùng AWS secrets. | Quân |
| **W3-07** | Full Week 3 Documentation & Runbook | Bộ tài liệu kế hoạch, báo cáo tiến độ, nghiên cứu Standard vs FIFO, hướng dẫn monitoring/benchmark/load-test, evidence index và AWS manual runbook. | Quân (kỹ thuật/runbook/report); Khôi (phối hợp review, evidence SNS) |

---

## 3. Phân công chi tiết theo thành viên

### 3.1. Phạm Minh Quân
- Thiết kế và triển khai `iac/week3-monitoring.yaml` cho `DLQVisibleMessagesAlarm` (`AWS/SQS`, `ApproximateNumberOfMessagesVisible >= 1`, `QueueName=orders-dlq`) và các alarm tùy chọn cho `order-consumer`.
- Xây dựng `scripts/collect_cloudwatch_metrics.py`, `scripts/benchmark_sqs.py`, `scripts/load_test_orders.py` và `scripts/generate_week3_report.py`.
- Viết bộ unit tests offline với mock đầy đủ cho các nhánh thành công, lỗi mạng/API, timeout, dữ liệu khuyết (`NO_DATA`), duplicate và bảo vệ queue production.
- Thiết lập `.github/workflows/python-tests.yml`.
- Thực hiện chạy thật trên AWS Learner Lab theo `docs/week3-aws-manual-runbook.md`, thu thập metrics/screenshots và cập nhật báo cáo kỹ thuật.

### 3.2. Nguyễn Đoàn Minh Khôi
- Cung cấp và đối soát ARN của SNS Topic `order-dlq-alert` cùng trạng thái `Confirmed` của email subscription trên AWS Learner Lab.
- Phối hợp kiểm tra tính tương thích của `order-api` (`POST /orders`) và `order-producer` khi chạy `scripts/load_test_orders.py`.
- Xác minh nhận email cảnh báo thực tế khi `DLQVisibleMessagesAlarm` chuyển sang trạng thái `ALARM` và chụp ảnh bằng chứng (che thông tin email cá nhân/Account ID).

---

## 4. Tiêu chí nghiệm thu (Acceptance Criteria)

1. **An toàn mặc định (Offline-first & Safety Guardrails):**
   - Các CLI kết nối AWS/HTTP mặc định không gọi mạng. Benchmark/load yêu cầu `--execute` cùng `--confirm-target` khớp queue/hostname; collector CloudWatch chỉ đọc dùng `--execute`. Cặp `--dry-run --execute` bị từ chối.
   - `scripts/benchmark_sqs.py` từ chối mọi thao tác lên `orders-queue` và `orders-dlq` để bảo vệ luồng chính.
   - Không tạo IAM User/Role mới; không hard-code AWS Account ID, ARN cá nhân hoặc endpoint cũ trong code/script.
2. **Độ chính xác ngữ nghĩa:**
   - Phân biệt rõ `SQS API benchmark` (W3-02) với `Full Pipeline E2E load test` (W3-03).
   - Phân biệt rõ `HTTP 202 Accepted` (Producer đã gửi SQS) với `DynamoDB status = PROCESSED` (Consumer đã lưu DB).
   - Không tự gán `0` cho các CloudWatch datapoint bị khuyết (`NO_DATA`).
3. **Kiểm thử & Hồi quy:**
   - Giữ nguyên 33 unit test methods của Tuần 2 (`tests/test_producer.py` + `tests/test_consumer.py`).
   - Toàn bộ unit tests mới cho W3-01..W3-04 chạy PASS hoàn toàn offline.
4. **Quy tắc ghi nhận:**
   - Chỉ ghi kết quả có bằng chứng thực tế và đúng người thực hiện.

---

## 5. Phụ thuộc & Rủi ro (Dependencies & Risks)

| Rủi ro / Phụ thuộc | Mức độ | Biện pháp giảm thiểu |
|---|---|---|
| Phiên AWS Learner Lab hết hạn hoặc đổi URL API Gateway | Trung bình | Toàn bộ URL/ARN được truyền qua tham số CLI (`--endpoint`, `--queue-url`, `AlertSnsTopicArn`); không hard-code. |
| Giới hạn tổng Lambda concurrency `<= 10` trên Learner Lab | Cao | `scripts/load_test_orders.py` giới hạn cứng `rate <= 10 req/s` và `count <= 100` (mặc định `count=10, rate=2.0`). |
| Quyền CloudFormation trên Learner Lab bị hạn chế một phần | Thấp | Template chỉ tạo `AWS::CloudWatch::Alarm` (không tạo IAM hay SNS); kèm lệnh AWS CLI `put-metric-alarm` tương đương trong runbook. |
| Độ trễ xuất hiện metric CloudWatch (1–5 phút) | Trung bình | Sử dụng cửa sổ quan sát cấu hình được (`--window-minutes 30`, `--period 60`) và ghi nhận `NO_DATA` trung thực nếu metric chưa xuất hiện. |
