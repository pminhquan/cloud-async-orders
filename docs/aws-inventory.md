# Danh mục AWS qua bốn tuần

> Các mục 1–5 giữ inventory lịch sử Tuần 1–2. Inventory mới ngày 29/10/2026 thuộc Lab Quân, được đối chiếu riêng tại [báo cáo Tuần 4](week4-report.md); không mặc định tài nguyên Lab Khôi có trên Lab Quân.

## 1. Quy ước chung

- Region: `us-east-1`
- Lambda execution role: `LabRole`
- Không tạo IAM User/Role mới.
- Tags quy ước:
  - `Project=AsyncOrderProcessing`
  - `Owner=Khoi-Quan`

---

## 2. Tài nguyên chính

| Tài nguyên | Dịch vụ | Vai trò | Trạng thái đến Tuần 2 |
|---|---|---|---|
| `order-api` | API Gateway | Endpoint `POST /orders` | Đã dùng trong E2E |
| `order-producer` | Lambda | Validate request, tạo order, gửi SQS | Hoàn thiện Tuần 2 |
| `orders-queue` | SQS Standard | Queue chính | Đã tích hợp Producer/Consumer |
| `orders-dlq` | SQS Standard | Dead Letter Queue | Retry/DLQ PASS trên Lab Quân |
| `order-consumer` | Lambda | Validate message, idempotency, ghi DynamoDB | Hoàn thiện Tuần 2 |
| `Orders` | DynamoDB | Lưu order theo `orderId` | Đã ghi `PROCESSED` |
| `order-dlq-alert` | SNS | Topic cảnh báo | Đã tạo từ Tuần 1; alarm hoàn chỉnh thuộc giai đoạn sau |

---

## 3. Trạng thái Tuần 1

### Phía Quân

- SQS/DLQ/Consumer PoC hoạt động.
- Retry/DLQ PoC hoạt động.
- Consumer chủ yếu validate/log, chưa ghi DynamoDB.

### Phía Khôi

- DynamoDB `Orders` đã tạo.
- Producer PoC nhận request và trả `202`.
- API `POST /orders` hoạt động.
- SNS topic/email đã tạo.
- Producer chưa gửi SQS thật.

### Kết luận

Chưa Full E2E.

---

## 4. Trạng thái Tuần 2

### Producer

- `QUEUE_URL` trỏ `orders-queue`.
- Producer gọi `sqs.send_message()`.
- Valid → `202`.
- Invalid → `400`.
- Invalid không enqueue.

### Consumer

- `TABLE_NAME=Orders`.
- Consumer ghi DynamoDB.
- Conditional write + idempotency.
- `ORDER_CONFLICT`.

### Trigger

Trong quá trình debug Lab Khôi, trigger từng bị `Disabled`, đây là nguyên nhân order E2E cũ nằm backlog. Sau đó nhóm dùng Lab Quân làm môi trường integration chính để hoàn tất Full E2E.

Cấu hình test Tuần 2 được dùng ở các giai đoạn khác nhau; khi đọc ảnh cần đối chiếu timestamp/ghi chú thay vì giả định một giá trị duy nhất cho toàn bộ tuần.

### Retry/DLQ

- Redrive `orders-queue` → `orders-dlq`.
- Test Tuần 2 phía Quân dùng `maxReceiveCount=5`.
- Invalid JSON được retry và chuyển DLQ.

---

## 5. Evidence

- Tuần 1: [evidence/week1/README.md](evidence/week1/README.md)
- Tuần 2: [evidence/week2/README.md](evidence/week2/README.md)

## 6. Đối chiếu Tuần 3–4

- [Minh chứng Tuần 3](evidence/week3/README.md): benchmark, E2E/load, batch thật; SNS/Alarm thủ công thuộc Lab Khôi.
- Ngày 29/10 trên Lab Quân: Producer cập nhật đúng main; ESM đúng nguồn đã Enabled; timeout 3s/memory 128 MB giữ nguyên; Orders ACTIVE/PAY_PER_REQUEST.
- Kiểm tra cuối: orders-queue 0/0/0; orders-dlq tăng từ 2 lên 3 sau một sentinel thử mới, phù hợp với redrive trong phạm vi bằng chứng tương quan; hai queue benchmark rỗng được giữ để xem xét sau demo.
- Không có project alarm/topic trên Lab Quân. Log groups được giữ nguyên, chưa đặt retention. Không tạo/xóa IAM, purge hoặc destructive cleanup.
- Trạng thái nguồn và rollback, ma trận kiểm thử, metrics và KEEP/REVIEW nằm trong [báo cáo Tuần 4](week4-report.md).
- Bổ sung ngày 30/10: đã đối chiếu lại cấu hình, mapping Consumer Enabled, SNS email confirmed và stack monitoring chứa một alarm DLQ; metric tự kích hoạt ALARM và email đã khớp. [Cấu hình/kết quả sau cập nhật](week4-report.md#71-kết-quả-sau-cập-nhật-đã-được-phê-duyệt).
