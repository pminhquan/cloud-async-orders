# Minh chứng Tuần 3

Dữ liệu thực nghiệm ngày 24/10/2026, `us-east-1`. B1/B2/B3 thuộc Lab Quân; SNS/Alarm thuộc Lab Khôi. Kết quả và giới hạn chi tiết: [báo cáo Tuần 3](../../week3-report.md).

## 1. Phạm Minh Quân (Lab Quân)

### B1 — Benchmark SQS Standard/FIFO

- [Manifest](quan/b1-2026-10-24/manifest.json)
- [Standard — summary](quan/b1-2026-10-24/standard/benchmark-summary.json) · [CSV](quan/b1-2026-10-24/standard/benchmark-results.csv)
- [FIFO 1 group — summary](quan/b1-2026-10-24/fifo-single/benchmark-summary.json) · [CSV](quan/b1-2026-10-24/fifo-single/benchmark-results.csv)
- [FIFO 5 group — summary](quan/b1-2026-10-24/fifo-multi/benchmark-summary.json) · [CSV](quan/b1-2026-10-24/fifo-multi/benchmark-results.csv)
- Phân tích: [week3-quan-b1-results.md](../../week3-quan-b1-results.md)

### B2 — Load test và đối soát DynamoDB

- [Load summary](quan/b2-2026-10-24/load/load-test-summary.json) · [CSV](quan/b2-2026-10-24/load/load-test-results.csv)
- [CloudWatch metrics](quan/b2-2026-10-24/metrics/cloudwatch-metrics-summary.json) · [CSV](quan/b2-2026-10-24/metrics/cloudwatch-metrics-results.csv)
- Ảnh Console: [API results](quan/b2-2026-10-24/screenshots/W3-B2-API-Recorded-Results.jpg) · [CloudWatch Consumer](quan/b2-2026-10-24/screenshots/W3-B2-CloudWatch-Consumer.jpg) · [Consumer Disabled](quan/b2-2026-10-24/screenshots/W3-B2-Consumer-Disabled.jpg) · [DynamoDB order](quan/b2-2026-10-24/screenshots/W3-B2-DynamoDB-Console-Order.jpg) · [DynamoDB GetItem](quan/b2-2026-10-24/screenshots/W3-B2-DynamoDB-Recorded-GetItem.jpg)
- [Provenance ảnh](quan/b2-2026-10-24/screenshots/screenshots-provenance.json)

### B3 — Batch thật

- [Batch proof](quan/b3-2026-10-24/batch-proof.json)
- [Execution log](quan/b3-2026-10-24/b3-execution-log.json)
- [Trạng thái cuối](quan/b3-2026-10-24/final-state-check.json)
- [Load summary](quan/b3-2026-10-24/load/load-test-summary.json)
- [Ảnh CloudWatch hai record](quan/b3-2026-10-24/screenshots/W3-B3-CloudWatch-Two-Record-Batch.jpg)
- [Provenance ảnh](quan/b3-2026-10-24/screenshots/screenshots-provenance.json)

## 2. Nguyễn Đoàn Minh Khôi (Lab Khôi)

- [Tổng hợp phạm vi SNS/Alarm](../../week3-khoi-evidence.md)
- Ảnh: [Alarm history](khoi/W3-CW-DLQ-Alarm-History.png) · [SNS subscription](khoi/W3-SNS-Topic-Subscription-Confirmed.png) · [SNS publish](khoi/W3-SNS-Topic-Publish-Success.png) · [Email thường](khoi/W3-SNS-Email-Received.png) · [Email cảnh báo](khoi/W3-SNS-Alarm-Email-Received.png) · [API 202](khoi/W3-Khoi-API-POST-202.png) · [API 400](khoi/W3-Khoi-API-Invalid-400.png) · [DynamoDB PROCESSED](khoi/W3-Khoi-DynamoDB-Order-Processed.png)

## 3. Quy tắc đọc minh chứng

- Giữ JSON/CSV cùng `runId` để đối chiếu với ảnh; không dùng ảnh Tuần 1–2 thay cho phép đo Tuần 3.
- Phân biệt SQS API benchmark (B1), API load (B2), batch thật (B3) và unit test offline.
- Alarm → SNS → email là phép thử trạng thái thủ công, không chứng minh DLQ metric tự kích hoạt.
- Không suy diễn số liệu khi datapoint thiếu; giá trị `NO_DATA` không đổi thành `0`.
- Ảnh đã che/crop thông tin không cần thiết; không lưu credential, token, receipt handle.
