# Tuần 2 — Evidence của Nguyễn Đoàn Minh Khôi

## Mục tiêu

Chứng minh Producer đã có input validation và invalid request không được enqueue vào SQS.

## Danh sách ảnh

1. `01-producer-valid-202.png` — valid payload → HTTP `202`, có `ORDER_SENT_TO_SQS`.
2. `02-producer-missing-customerid-400.png` — thiếu `customerId` → `400`.
3. `03-producer-missing-productid-400.png` — thiếu `productId` → `400`.
4. `04-producer-invalid-quantity-400-a.png` — invalid quantity → `400`.
5. `05-producer-invalid-quantity-400-b.png` — invalid quantity → `400`.
6. `06-producer-invalid-quantity-400-c.png` — invalid quantity → `400`.
7. `07-producer-invalid-json-400.png` — malformed JSON → `400`.
8. `08-sqs-before-invalid-request.png` — trước test: `Messages available = 8`, `in flight = 0`.
9. `09-producer-invalid-request-400.png` — invalid request dùng để kiểm tra không enqueue.
10. `10-sqs-after-invalid-request.png` — sau test vẫn `Messages available = 8`, `in flight = 0`.

## Kết luận

```text
Valid request   → 202 → được phép SendMessage
Invalid request → 400 → không enqueue
```

Số message SQS không tăng trong test invalid request.
