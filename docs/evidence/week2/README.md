# Chỉ mục minh chứng Tuần 2

## 1. Mục đích

Phân biệt rõ evidence theo môi trường để tránh tuyên bố một test đã chạy ở cả hai Lab khi thực tế chỉ chạy ở một Lab.

---

## 2. Evidence Nguyễn Đoàn Minh Khôi — có trong working tree này

Thư mục:

```text
screenshots/week2/khoi/
```

| File | Nội dung |
|---|---|
| `01-producer-valid-202.png` | Producer valid → `202`, log `ORDER_SENT_TO_SQS` |
| `02-producer-missing-customerid-400.png` | thiếu `customerId` → `400` |
| `03-producer-missing-productid-400.png` | thiếu `productId` → `400` |
| `04-producer-invalid-quantity-400-a.png` | invalid quantity → `400` |
| `05-producer-invalid-quantity-400-b.png` | invalid quantity → `400` |
| `06-producer-invalid-quantity-400-c.png` | invalid quantity → `400` |
| `07-producer-invalid-json-400.png` | malformed JSON → `400` |
| `08-sqs-before-invalid-request.png` | SQS trước invalid: 8 available / 0 in flight |
| `09-producer-invalid-request-400.png` | invalid request dùng test không enqueue |
| `10-sqs-after-invalid-request.png` | SQS sau invalid vẫn 8 available / 0 in flight |

Kết luận evidence Khôi:
- Producer validation: PASS.
- Invalid request không enqueue: PASS.

---

## 3. Evidence Phạm Minh Quân — bộ 19 ảnh

Theo tiến độ nhóm, Quân đã push bộ **19 ảnh AWS thật** lên branch/PR tài liệu Tuần 2.

Nhóm evidence:
- Consumer trigger.
- Consumer direct test.
- DynamoDB item `PROCESSED`.
- Full E2E cùng `orderId`.
- Idempotency replay.
- `ORDER_CONFLICT`.
- DynamoDB không overwrite item conflict.
- Invalid JSON CloudWatch log.
- Redrive policy.
- DLQ message.
- Batch valid.
- Mixed batch/replay.
- Small load 10 request.
- 10 item `PROCESSED`.

PR tài liệu:

```text
https://github.com/pminhquan/cloud-async-orders/pull/6
```

> Nếu 19 ảnh chưa xuất hiện trong working tree hiện tại, cần pull/copy từ branch tài liệu PR #6 trước khi muốn repository local chứa đầy đủ evidence của cả hai người.

---

## 4. Evidence quan trọng cần dùng trong báo cáo

### Producer
- valid `202`;
- invalid `400`;
- SQS before/after invalid không tăng.

### Full E2E
- API response có `orderId`;
- DynamoDB có cùng `orderId` và `PROCESSED`.

### Retry/DLQ
- CloudWatch `INVALID_JSON`;
- DLQ có đúng message/body hoặc message ID.

### Idempotency
- replay cùng payload thành công;
- conflict khác payload báo `ORDER_CONFLICT`;
- item DB không bị ghi đè.

### Load
- 10/10 request `202`;
- 10 item `PROCESSED`.
