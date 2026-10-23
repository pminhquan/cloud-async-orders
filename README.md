# cloud-async-orders

Dự án môn **Điện toán đám mây**: **Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda**.

- **Môn học:** CLC0332779_05UTExMC - Điện toán đám mây
- **GVHD:** TS. Huỳnh Xuân Phụng
- **Nhóm:** Serverless
- **Thành viên:**
  - 24110311 — Phạm Minh Quân
  - 24110259 — Nguyễn Đoàn Minh Khôi
- **AWS Region:** `us-east-1`
- **IAM:** dùng `LabRole` có sẵn trong AWS Learner Lab, không tạo IAM User/Role mới.

---

## 1. Mục tiêu hệ thống

Hệ thống tiếp nhận đơn hàng qua API, đưa đơn vào hàng đợi để xử lý bất đồng bộ, lưu trạng thái vào DynamoDB và cô lập message lỗi bằng DLQ, đồng thời giám sát/cảnh báo qua CloudWatch Alarm + SNS.

```text
Client
  ↓
API Gateway
  ↓
order-producer
  ↓
orders-queue
  ↓
order-consumer
  ↓
DynamoDB Orders

Invalid / failed message
  ↓
Retry
  ↓
orders-dlq
  ↓
CloudWatch Alarm → SNS (order-dlq-alert) → Email
```

---

## 2. Tiến độ theo tuần

### Tuần 1 — Nền tảng và PoC riêng từng phía

Tuần 1 tập trung nghiên cứu dịch vụ, thiết kế kiến trúc và dựng các PoC độc lập.

**Phạm Minh Quân:**
- SQS Standard `orders-queue`.
- DLQ `orders-dlq`.
- Consumer Lambda PoC.
- Test valid / invalid / retry / DLQ.
- Nghiên cứu Standard/FIFO.
- Sơ đồ kiến trúc.

**Nguyễn Đoàn Minh Khôi:**
- DynamoDB `Orders`.
- Producer Lambda `order-producer` PoC.
- API Gateway `order-api`, route `POST /orders`.
- Test API trả HTTP `202`.
- SNS topic `order-dlq-alert` và email subscription.

**Kết luận Tuần 1:** các thành phần đã được test riêng nhưng **chưa có Full E2E** `Producer → SQS → Consumer → DynamoDB`.

Tài liệu:
- [Báo cáo Tuần 1](docs/week1-report.md)
- [Kế hoạch Tuần 1](docs/week1-plan.md)
- [Công việc và minh chứng Tuần 1](docs/worklog/week1.md)
- [Minh chứng Tuần 1](docs/evidence/week1/README.md)

### Tuần 2 — Tích hợp hoàn chỉnh và kiểm thử

Tuần 2 nâng cấp Producer/Consumer và hoàn thiện luồng xử lý.

**Producer:**
- Gửi message thật vào SQS.
- Validate input.
- Valid request → `202`.
- Invalid request → `400`.
- Invalid request không enqueue SQS.

**Consumer:**
- Validate schema phẳng.
- Ghi DynamoDB `Orders` với `status = PROCESSED`.
- Idempotency bằng conditional write `attribute_not_exists(orderId)`.
- Phát hiện `ORDER_CONFLICT` khi cùng `orderId` nhưng business payload khác.

**Kiểm thử:**
- Full E2E API → Producer → SQS → Consumer → DynamoDB: PASS trên Lab Quân.
- Idempotency: PASS.
- ORDER_CONFLICT: PASS.
- Invalid JSON → Retry → DLQ: PASS.
- Direct batch valid/mixed/replay: PASS theo thiết kế full-batch failure.
- Small load test 10 request: 10/10 HTTP `202`, 10 item `PROCESSED` trên Lab Quân.
- Producer validation trên Lab Khôi: PASS, có 10 ảnh minh chứng local.

Tài liệu:
- [Báo cáo Tuần 2](docs/week2-report.md)
- [Kế hoạch Tuần 2](docs/week2-plan.md)
- [Công việc và minh chứng Tuần 2](docs/worklog/week2.md)
- [Minh chứng Tuần 2](docs/evidence/week2/README.md)

### Tuần 3 — Giám sát CloudWatch/SNS, Benchmark Standard vs FIFO & Controlled Load Test

Tuần 3 bổ sung hạ tầng giám sát dưới dạng code (IaC), bộ công cụ đo kiểm tự động hóa có chốt an toàn (`--dry-run` mặc định), kiểm thử hồi quy và CI:

- **CloudWatch Monitoring & SNS Alert (`W3-01`):** Template [`iac/week3-monitoring.yaml`](iac/week3-monitoring.yaml) định nghĩa `DLQVisibleMessagesAlarm` (`ApproximateNumberOfMessagesVisible >= 1` trên `orders-dlq`, `TreatMissingData=notBreaching`) kết nối tới SNS Topic `order-dlq-alert` hiện có, kèm [`scripts/collect_cloudwatch_metrics.py`](scripts/collect_cloudwatch_metrics.py).
- **SQS Standard vs FIFO Benchmark (`W3-02`):** Công cụ [`scripts/benchmark_sqs.py`](scripts/benchmark_sqs.py) đo thông lượng, độ trễ (`mean/median/p95`), duplicate và thứ tự nhận (`single-group` vs `multi-group`) trên queue thử nghiệm riêng, chặn cứng việc ghi/xóa trên `orders-queue` và `orders-dlq`.
- **Controlled Load Test & DynamoDB Reconciliation (`W3-03`):** Công cụ [`scripts/load_test_orders.py`](scripts/load_test_orders.py) gửi tải trong giới hạn concurrency `<= 10` và đối soát read-only `GetItem` theo từng `orderId` để xác minh `status = PROCESSED`.
- **Report Generator, Unit Tests & CI (`W3-04..W3-06`):** Công cụ [`scripts/generate_week3_report.py`](scripts/generate_week3_report.py), bổ sung tests hồi quy và tests công cụ offline, và thiết lập [`.github/workflows/python-tests.yml`](.github/workflows/python-tests.yml).
- **Hướng dẫn thao tác:** [`docs/week3-aws-manual-runbook.md`](docs/week3-aws-manual-runbook.md).

Tài liệu Tuần 3:
- [Kế hoạch Tuần 3](docs/week3-plan.md)
- [Báo cáo Tuần 3](docs/week3-report.md)
- [Thiết kế Giám sát CloudWatch & SNS](docs/week3-monitoring.md)
- [Thiết kế Benchmark Standard vs FIFO](docs/week3-benchmark.md)
- [Thiết kế Controlled Load Test & Reconciliation](docs/week3-load-testing.md)
- [AWS Manual Runbook (Dành cho Quân & Khôi)](docs/week3-aws-manual-runbook.md)
- [Chỉ mục Minh chứng Tuần 3](docs/evidence/week3/README.md)
- [Bàn giao Kỹ thuật Tuần 3](docs/WEEK3_AGENT_HANDOFF.md)

---

## 3. Schema message Tuần 2–3

```json
{
  "orderId": "UUID",
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2,
  "status": "PENDING",
  "createdAt": "2026-10-15T00:00:00+00:00"
}
```

Quy ước:
- Producer tạo `orderId` và `createdAt`.
- Producer gửi `status = PENDING`.
- Consumer validate đủ field.
- Consumer ghi DynamoDB với `status = PROCESSED`.

Chi tiết: [Integration Contract](docs/integration-contract.md).

---

## 4. Cấu trúc repository

```text
cloud-async-orders/
├── .github/
│   └── workflows/
│       └── python-tests.yml
├── src/
│   ├── producer/
│   │   └── lambda_function.py
│   └── consumer/
│       └── lambda_function.py
├── tests/
│   ├── fixtures/
│   ├── test_producer.py
│   ├── test_consumer.py
│   ├── test_monitoring_and_metrics.py
│   ├── test_benchmark_sqs.py
│   └── test_load_test_orders.py
├── scripts/
│   ├── test-order-api.ps1
│   ├── collect_cloudwatch_metrics.py
│   ├── benchmark_sqs.py
│   ├── load_test_orders.py
│   └── generate_week3_report.py
├── docs/
│   ├── architecture/
│   ├── evidence/
│   │   ├── week1/
│   │   ├── week2/
│   │   └── week3/
│   ├── research/
│   ├── worklog/
│   │   ├── week1.md
│   │   ├── week2.md
│   │   └── week3.md
│   ├── requirements.md
│   ├── task-assignment.md
│   ├── integration-contract.md
│   ├── aws-inventory.md
│   ├── week1-plan.md
│   ├── week1-report.md
│   ├── week2-plan.md
│   ├── week2-report.md
│   ├── week3-plan.md
│   ├── week3-report.md
│   ├── week3-monitoring.md
│   ├── week3-benchmark.md
│   ├── week3-load-testing.md
│   ├── week3-aws-manual-runbook.md
│   └── WEEK3_AGENT_HANDOFF.md
├── screenshots/
│   ├── week1/
│   └── week2/
│       └── khoi/
├── iac/
│   ├── README.md
│   └── week3-monitoring.yaml
└── README.md
```

---

## 5. Chạy unit tests (Offline)

```bash
python -m pytest -q
# Hoặc dùng stdlib unittest:
python -B -m unittest discover -s tests -p "test_*.py"
python -m compileall -q src scripts tests
```

Kết quả kiểm thử và các lệnh đã chạy được ghi trong [báo cáo offline Tuần 3](docs/week3-report.md).

---

## 6. Kiểm thử API & Công cụ Tuần 3

Kiểm tra nhanh CLI ở chế độ an toàn `--dry-run` (không gọi AWS):

```bash
python scripts/collect_cloudwatch_metrics.py --dry-run
python scripts/benchmark_sqs.py --queue-type standard --queue-url orders-benchmark-standard --dry-run
python scripts/load_test_orders.py --endpoint https://example-api.execute-api.us-east-1.amazonaws.com/orders --dry-run
```

Script PowerShell smoke test (yêu cầu truyền `-EndpointUrl` và `-Execute` khi gửi thật):

```powershell
./scripts/test-order-api.ps1 -EndpointUrl "https://<api-id>.execute-api.us-east-1.amazonaws.com/orders"
```

---

## 7. Bảo mật khi Public repository

Không commit:
- AWS Access Key
- Secret Access Key
- Session Token
- Password
- File credentials
- Thông tin đăng nhập Learner Lab

Ảnh minh chứng trước khi public cần rà soát email, Account ID và thông tin cá nhân không cần thiết.

---

## 8. Ma trận đối chiếu nhanh

- [Ma trận từng yêu cầu → người thực hiện → kết quả → ảnh/code (Tuần 1–2)](docs/TRACEABILITY-W1-W2.md).
- [Chỉ mục 29 ảnh kiểm thử Tuần 2](docs/evidence/week2/README.md).
- [Báo cáo tiến độ và trạng thái Tuần 3](docs/week3-report.md).
