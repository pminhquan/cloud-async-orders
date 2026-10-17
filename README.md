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

Hệ thống tiếp nhận đơn hàng qua API, đưa đơn vào hàng đợi để xử lý bất đồng bộ, lưu trạng thái vào DynamoDB và cô lập message lỗi bằng DLQ.

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
```

Mục tiêu cuối kỳ còn bao gồm giám sát/cảnh báo CloudWatch + SNS và so sánh SQS Standard/FIFO.

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
- [Worklog Tuần 1](docs/worklog/week1.md)
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
- [Worklog Tuần 2](docs/worklog/week2.md)
- [Minh chứng Tuần 2](docs/evidence/week2/README.md)

---

## 3. Schema message Tuần 2

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
├── src/
│   ├── producer/
│   │   └── lambda_function.py
│   └── consumer/
│       └── lambda_function.py
├── tests/
│   ├── fixtures/
│   ├── test_producer.py
│   └── test_consumer.py
├── scripts/
│   └── test-order-api.ps1
├── docs/
│   ├── architecture/
│   ├── evidence/
│   │   ├── week1/
│   │   └── week2/
│   ├── research/
│   ├── worklog/
│   │   ├── week1.md
│   │   └── week2.md
│   ├── requirements.md
│   ├── task-assignment.md
│   ├── integration-contract.md
│   ├── aws-inventory.md
│   ├── week1-plan.md
│   ├── week1-report.md
│   ├── week2-plan.md
│   └── week2-report.md
├── screenshots/
│   ├── week1/
│   └── week2/
│       └── khoi/
├── iac/
└── README.md
```

---

## 5. Chạy unit tests

```bash
python -m pytest -q
```

Trạng thái trên bộ source hiện tại:

```text
33 passed, 81 subtests passed (kết quả đã ghi nhận trên bộ mã nguồn trước; chưa chạy lại trên máy Khôi sau khi tạo PR #8)
```

---

## 6. Kiểm thử API

Request hợp lệ:

```json
{
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2
}
```

Kỳ vọng:

```text
HTTP 202
```

Các request thiếu `customerId`, thiếu `productId`, `quantity <= 0`, `quantity` sai kiểu hoặc malformed JSON phải trả:

```text
HTTP 400
```

Script hỗ trợ:

```powershell
./scripts/test-order-api.ps1
```

---

## 7. GitHub / Pull Request Tuần 2

- PR #5 — Consumer + DynamoDB + idempotency: **Merged**.
- PR #7 — Producer + SQS + validation: **Merged**.
- PR #6 — tài liệu/evidence Tuần 2: trạng thái cần kiểm tra lại trước khi nộp cuối.

Các hash đã ghi nhận trong quá trình làm:

```text
Consumer source commit: 0192d2b
Consumer merge commit:  914de9b
Producer SQS commit:     e04e1f2
Producer validation:     835c840
Producer squash main:    015d420
```

> Nếu GitHub hiện tại có hash khác do rebase/squash bổ sung, ưu tiên lịch sử thực tế trên GitHub tại thời điểm nộp.

---

## 8. Bảo mật khi Public repository

Không commit:
- AWS Access Key
- Secret Access Key
- Session Token
- Password
- File credentials
- Thông tin đăng nhập Learner Lab

Ảnh minh chứng trước khi public cần rà soát email, Account ID và thông tin cá nhân không cần thiết.

---

## 9. Checklist trước khi nộp Tuần 2

- [x] Source Producer.
- [x] Source Consumer.
- [x] Producer validation.
- [x] Consumer idempotency.
- [x] Unit tests.
- [x] Full E2E có evidence trên Lab Quân.
- [x] Retry/DLQ có evidence trên Lab Quân.
- [x] Producer validation có evidence trên Lab Khôi.
- [x] Người nộp báo cáo nhóm đã đáp ứng yêu cầu tối thiểu 8 giờ/người/tuần; phân bổ giờ chi tiết chưa được đối soát.
- [ ] Xác nhận khai báo AI của từng thành viên.
- [ ] Kiểm tra lại link GitHub/PR/evidence sau push cuối.
- [x] 19 ảnh AWS của Quân đã được đồng bộ từ PR #6 vào nhánh PR #8; PR #6 vẫn cần được nhóm quyết định đóng/merge để tránh tài liệu trùng.

## 10. Ma trận đối chiếu nhanh

- [Ma trận từng yêu cầu → người thực hiện → kết quả → ảnh/code](docs/TRACEABILITY-W1-W2.md).
- [Chỉ mục 29 ảnh kiểm thử Tuần 2](docs/evidence/week2/README.md).
