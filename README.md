# cloud-async-orders

Hệ thống xử lý đơn hàng bất đồng bộ trên AWS: API Gateway → Lambda Producer → SQS → Lambda Consumer → DynamoDB, kèm retry/DLQ, CloudWatch và SNS.

- **Môn học:** CLC0332779_05UTExMC — Điện toán đám mây, HCMUTE
- **GVHD:** TS. Huỳnh Xuân Phụng
- **Nhóm:** Serverless — Phạm Minh Quân (24110311), Nguyễn Đoàn Minh Khôi (24110259)
- **AWS Region:** `us-east-1`
- **IAM:** `LabRole` có sẵn trong AWS Academy Learner Lab; không tạo IAM User/Role mới

## 1. Kiến trúc

```text
Client
  ↓
API Gateway (POST /orders)
  ↓
order-producer (Lambda)
  ↓
orders-queue (SQS Standard)
  ↓
order-consumer (Lambda)
  ↓
DynamoDB Orders (status = PROCESSED)

Message lỗi → retry theo maxReceiveCount=5 → orders-dlq
orders-dlq → CloudWatch Alarm → SNS order-dlq-alert → Email
```

Chi tiết: [Kiến trúc](docs/architecture/README.md) · [Integration Contract](docs/integration-contract.md).

## 2. Dịch vụ AWS

| Dịch vụ | Vai trò |
|---|---|
| API Gateway (HTTP API) | Endpoint `POST /orders` |
| Lambda Producer | Validate request, tạo `orderId`, gửi SQS, trả `202/400/500` |
| SQS Standard + DLQ | Đệm xử lý, retry và cô lập message lỗi |
| Lambda Consumer | Validate message, ghi DynamoDB, idempotency/conflict |
| DynamoDB `Orders` | Lưu đơn theo `orderId`, trạng thái `PROCESSED` |
| CloudWatch | Logs, metrics và alarm DLQ |
| SNS | Phân phối cảnh báo qua email |

## 3. Chức năng chính

- Request hợp lệ trả `202`; request sai schema hoặc JSON trả `400` và không enqueue; lỗi gửi SQS trả `500`.
- Consumer dùng conditional write `attribute_not_exists(orderId)`, đọc lại với `ConsistentRead=True` để phân biệt replay hợp lệ với `ORDER_CONFLICT`.
- Full-batch failure semantics: một record lỗi làm invocation thất bại để SQS retry; chưa bật `ReportBatchItemFailures`.
- Công cụ offline-first: benchmark SQS, load test + đối soát DynamoDB, thu thập metrics và sinh báo cáo.
- Template CloudFormation cho alarm DLQ; CI chạy pytest, unittest, compileall, cfn-lint và CLI dry-run.

## 4. Cấu trúc repository

```text
cloud-async-orders/
├── .github/workflows/python-tests.yml
├── src/
│   ├── producer/lambda_function.py
│   └── consumer/lambda_function.py
├── tests/
├── scripts/
├── iac/
│   ├── week3-monitoring.yaml
│   └── README.md
├── docs/
│   ├── architecture/
│   ├── research/
│   ├── evidence/
│   │   ├── week1/ (sv1, sv2)
│   │   ├── week2/ (ảnh Quân và khoi/)
│   │   ├── week3/ (khoi/, quan/)
│   │   └── week4/
│   ├── worklog/
│   ├── requirements.md
│   ├── task-assignment.md
│   ├── integration-contract.md
│   ├── aws-inventory.md
│   ├── traceability.md
│   ├── week1-plan.md, week1-report.md
│   ├── week2-plan.md, week2-report.md
│   ├── week3-plan.md, week3-report.md
│   ├── week3-monitoring.md, week3-benchmark.md, week3-load-testing.md
│   ├── week3-aws-manual-runbook.md, week3-khoi-evidence.md, week3-quan-b1-results.md
│   ├── week4-plan.md, week4-report.md, week4-execution.md, week4-cost-analysis.md
│   ├── final-report.md, demo-script.md, SUBMISSION.md, ai-declaration.md
│   └── README.md
├── screenshots/ (bản sao lịch sử ảnh Tuần 1 và README chỉ mục)
├── CONTRIBUTING.md
└── README.md
```

Ảnh minh chứng chuẩn nằm trong `docs/evidence/`; `docs/evidence/week2/khoi/` chứa bộ 10 ảnh Producer validation.

## 5. Cài đặt và kiểm thử offline

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install pytest boto3 pyyaml cfn-lint

python -m pytest -q
python -B -m unittest discover -s tests -p "test_*.py"
python -m compileall -q src scripts tests
cfn-lint iac/week3-monitoring.yaml
```

Kết quả hồi quy ngày 29/10/2026: **56 tests PASS, 114 subtests PASS**, unittest **56 tests OK**, compileall và cfn-lint thành công. Chi tiết: [kiểm thử offline Tuần 4](docs/evidence/week4/offline-validation.md).

Kiểm tra CLI an toàn (không gọi AWS):

```bash
python scripts/collect_cloudwatch_metrics.py --dry-run
python scripts/benchmark_sqs.py --queue-type standard --queue-url orders-benchmark-standard --dry-run
python scripts/load_test_orders.py --endpoint https://example-api.execute-api.us-east-1.amazonaws.com/orders --dry-run
```

## 6. Tiến độ bốn tuần

| Tuần | Kết quả chính |
|---|---|
| 1 | Nghiên cứu dịch vụ, dựng PoC độc lập SQS/DLQ/Consumer và API/Producer/DynamoDB/SNS; chưa Full E2E. |
| 2 | Tích hợp Producer → SQS → Consumer → DynamoDB; validation, idempotency, `ORDER_CONFLICT`, retry/DLQ; direct batch và load nhỏ 10 request. |
| 3 | Benchmark SQS Standard/FIFO 3 × 20 message; load 10/10 `202` + `PROCESSED`; batch thật 2 record cùng invocation; collector, alarm IaC và CI. |
| 4 | Đối chiếu deployment, sửa Producer drift, bật ESM; nghiệm thu 13/13 HTTP đúng kỳ vọng, replay/conflict, retry 5 lần → DLQ; báo cáo, chi phí và demo. |

## 7. Tài liệu và minh chứng

- Báo cáo cuối kỳ: [final-report.md](docs/final-report.md)
- Nghiệm thu Tuần 4: [week4-report.md](docs/week4-report.md) · [ma trận](docs/week4-execution.md) · [chi phí](docs/week4-cost-analysis.md)
- Kịch bản demo: [demo-script.md](docs/demo-script.md)
- Hồ sơ nộp: [SUBMISSION.md](docs/SUBMISSION.md)
- Minh chứng: [Tuần 1](docs/evidence/week1/README.md) · [Tuần 2](docs/evidence/week2/README.md) · [Tuần 3](docs/evidence/week3/README.md) · [Tuần 4](docs/evidence/week4/README.md)
- Đối chiếu yêu cầu: [traceability.md](docs/traceability.md)
- Khai báo AI: [ai-declaration.md](docs/ai-declaration.md)
- Quy ước đóng góp: [CONTRIBUTING.md](CONTRIBUTING.md)

## 8. Bảo mật và giới hạn

- Không commit AWS Access Key, Secret Key, Session Token, password hoặc thông tin đăng nhập Learner Lab.
- Ảnh minh chứng giữ MSSV/thông tin sinh viên theo yêu cầu học phần; che email, Account ID và ARN khi không cần thiết.
- API hiện chưa có authorization; phù hợp phạm vi thực hành, không phải cấu hình production.
- Hai AWS Learner Lab là hai môi trường độc lập. Alarm/SNS có minh chứng thủ công trên Lab Khôi; Lab Quân không có alarm của dự án tại thời điểm nghiệm thu.
- Video demo chưa được ghi nhận trong repository; [demo-script.md](docs/demo-script.md) là storyboard và checklist quay.
