# Integration Contract — Producer ↔ SQS ↔ Consumer ↔ DynamoDB

Tài liệu này là hợp đồng dữ liệu dùng từ Tuần 2.

## 1. API request

`POST /orders`

```json
{
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2
}
```

Ràng buộc:
- `customerId`: string không rỗng.
- `productId`: string không rỗng.
- `quantity`: integer > 0, không chấp nhận bool/string/float.

## 2. API response

### Hợp lệ

```text
HTTP 202
```

```json
{
  "message": "Order accepted",
  "order": {
    "orderId": "UUID",
    "customerId": "CUS001",
    "productId": "P001",
    "quantity": 2,
    "status": "PENDING",
    "createdAt": "ISO-8601 UTC"
  }
}
```

### Không hợp lệ

```text
HTTP 400
```

Các trường hợp: thiếu field, field rỗng, `quantity <= 0`, sai kiểu, malformed JSON.

### Lỗi gửi SQS

```text
HTTP 500
```

Producer không trả `202` nếu `SendMessage` thất bại.

## 3. SQS message body

Message body là JSON phẳng:

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

Extra fields được Consumer hiện tại cho phép nhưng 6 field trên là contract chính.

## 4. Consumer validation

Consumer yêu cầu:
- root là object;
- `orderId`, `customerId`, `productId`, `status`, `createdAt` là string không rỗng;
- `quantity` là integer > 0.

Invalid JSON → `INVALID_JSON`.
Invalid schema → `INVALID_SCHEMA`.

Consumer raise exception để invocation thất bại và SQS thực hiện retry/full-batch retry.

## 5. DynamoDB write

Table:

```text
Orders
```

Partition key:

```text
orderId
```

Consumer ghi:

```text
status = PROCESSED
```

Conditional write:

```text
attribute_not_exists(orderId)
```

## 6. Idempotency

Nếu `orderId` đã tồn tại:

1. Consumer đọc item hiện tại với `ConsistentRead=True`.
2. So sánh các business field:
   - `customerId`
   - `productId`
   - `quantity`
   - `createdAt`
3. Nếu giống nhau → coi là retry/duplicate hợp lệ, không ghi đè.
4. Nếu khác → `ORDER_CONFLICT`, invocation fail để không silently overwrite dữ liệu.

`status` không được dùng để kết luận conflict vì message retry có thể còn `PENDING` trong khi item DB đã là `PROCESSED`.

## 7. Retry / DLQ

- SQS trigger dùng full-batch failure semantics.
- `ReportBatchItemFailures` hiện không bật trong cấu hình Tuần 2.
- Invalid record làm invocation fail.
- Sau khi vượt `maxReceiveCount`, SQS chuyển message sang `orders-dlq`.

Giá trị đã dùng trong bài test Tuần 2 phía Quân:

```text
maxReceiveCount = 5
```

## 8. Batch

Source Consumer hỗ trợ nhiều record trong `event.Records`.

Direct Lambda tests đã xác minh:
- nhiều record hợp lệ → `processedCount` đúng;
- mixed batch có invalid JSON → invocation fail theo full-batch semantics;
- replay không ghi đè item đã xử lý.

Direct invocation này không được mô tả như bằng chứng SQS đã tự gom batch thực tế.
