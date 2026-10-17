# BÁO CÁO TIẾN ĐỘ TUẦN 2

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Môn học:** CLC0332779_05UTExMC - Điện toán đám mây  
**GVHD:** TS. Huỳnh Xuân Phụng  
**Region:** `us-east-1`

## 1. Thành viên

| MSSV | Họ tên |
|---|---|
| 24110311 | Phạm Minh Quân |
| 24110259 | Nguyễn Đoàn Minh Khôi |

## 2. Mục tiêu Tuần 2

- Producer gửi SQS thật.
- Consumer ghi DynamoDB.
- Hoàn thiện schema chung.
- Input validation `202/400`.
- Idempotency và conflict handling.
- Full E2E.
- Retry/DLQ.
- Batch/replay.
- Small load test.

## 2. Kết quả tổng hợp

| Hạng mục | Kết quả |
|---|---|
| Producer → SQS | PASS |
| Valid request → 202 | PASS |
| Invalid request → 400 | PASS |
| Invalid không enqueue | PASS |
| Consumer → DynamoDB | PASS |
| Idempotency | PASS |
| ORDER_CONFLICT | PASS |
| Full E2E | PASS trên Lab Quân |
| Invalid JSON → Retry → DLQ | PASS trên Lab Quân |
| Direct batch valid | PASS |
| Direct mixed/replay | PASS theo full-batch semantics |
| Small load test | PASS 10/10 trên Lab Quân |
| Consumer unit tests | 15/15 PASS theo PR #5 |
| Kết quả test đã ghi nhận trong bản source trước | 33 passed, 81 subtests passed; chưa chạy lại trên máy Khôi sau PR #8 |

## 4. Phần Nguyễn Đoàn Minh Khôi — Producer/API

Đã thực hiện:
- Producer dùng `boto3` SQS client.
- `QUEUE_URL` trỏ queue chính.
- Tạo UUID `orderId`.
- Tạo UTC `createdAt`.
- `status=PENDING`.
- `SendMessage` vào SQS.
- Input validation.

Kết quả kiểm thử:

| Case | Kết quả |
|---|---|
| Valid payload | `202`, có `ORDER_SENT_TO_SQS` |
| Missing `customerId` | `400` |
| Missing `productId` | `400` |
| `quantity=0` | `400` |
| `quantity<0` | `400` |
| `quantity` sai kiểu | `400` |
| Malformed JSON | `400` |
| Queue trước invalid | 8 available / 0 in flight |
| Queue sau invalid | 8 available / 0 in flight |

Kết luận: invalid request bị chặn trước `sqs.send_message()`.

Evidence local:

```text
screenshots/week2/khoi/
```

## 5. Phần Phạm Minh Quân — Consumer/DynamoDB/Retry

Consumer Tuần 2:
- validate schema phẳng;
- DynamoDB conditional write;
- idempotency;
- strongly consistent duplicate check;
- safe structured logging;
- full-batch failure semantics.

Kết quả chính:

### Full E2E

```text
API → Producer → SQS → Consumer → DynamoDB
```

Đối soát đã ghi nhận:

```text
orderId = e918c4af-3a9e-47c9-8a0c-13adbdfef82e
status  = PROCESSED
```

### Idempotency / Conflict

- Duplicate cùng business payload: success, không overwrite.
- Cùng `orderId=TEST-QUAN-W2-001` nhưng đổi `quantity` từ 2 → 3: `ORDER_CONFLICT`.
- DynamoDB giữ item cũ.

### Retry / DLQ

Invalid message:

```text
INVALID_MESSAGE_WEEK2
```

Message ID đã ghi nhận:

```text
aa25ffee-aa5a-40ef-a224-347ed5c01523
```

Consumer log `INVALID_JSON`; sau retry message đi `orders-dlq`.

### Batch direct invocation

- 2 valid records → `processedCount=2`.
- Mixed batch có invalid JSON → invocation fail.
- Replay tiếp tục fail ở invalid record, item valid không bị overwrite nhờ idempotency.

### Small load

- 10 request tuần tự.
- 10/10 HTTP `202`.
- DynamoDB filter `CUS-LOAD-W2`: 10 item `PROCESSED`.

Đây là small load test, không phải stress test.

## 6. Pull Request và commit

### Consumer PR #5

```text
https://github.com/pminhquan/cloud-async-orders/pull/5
```

```text
source commit: 0192d2b
merge commit:  914de9b
```

### Producer PR #7

```text
https://github.com/pminhquan/cloud-async-orders/pull/7
```

```text
SQS integration: e04e1f2
validation:      835c840
squash main:     015d420
```

### Documentation PR #6

```text
https://github.com/pminhquan/cloud-async-orders/pull/6
```

Trạng thái cần kiểm tra lại ngay trước khi nộp vì có thể thay đổi sau lần cập nhật cuối.

## 7. Evidence

- [Evidence Tuần 2](evidence/week2/README.md)
- [Ảnh Khôi](../screenshots/week2/khoi/README.md)

Bộ 19 ảnh Lab Quân đã được đồng bộ từ PR #6 vào `docs/evidence/week2/` trong gói cập nhật kèm theo. [Chỉ mục 29 ảnh Tuần 2](evidence/week2/README.md) có liên kết riêng từng ảnh.

## 8. AI hỗ trợ

ChatGPT hỗ trợ:
- giải thích SQS/Lambda/DynamoDB;
- gợi ý Producer/Consumer;
- validation;
- idempotency;
- troubleshooting;
- Test Event;
- phân tích backlog/DLQ;
- tổ chức evidence/report.

Nhóm trực tiếp triển khai, kiểm thử và xác nhận kết quả thực tế.

## 9. Worklog

Xem [worklog/week2.md](worklog/week2.md).

**Xác nhận của nhóm:** người nộp báo cáo cả hai đã đạt mức tối thiểu 8 giờ/người; hiện không có số giờ/ngày chi tiết để kiểm toán. Xem worklog, chỉ điền giờ chi tiết khi có dữ liệu thật.

## 10. Kết luận

Tuần 2 đã đạt mục tiêu tích hợp lõi. Producer, SQS, Consumer và DynamoDB đã hoạt động theo pipeline bất đồng bộ; validation, idempotency và DLQ đã được kiểm thử. Các phần CloudWatch Alarm/SNS alert hoàn chỉnh, benchmark Standard/FIFO và load lớn được chuyển sang tuần sau.


## Đối chiếu yêu cầu theo người thực hiện và bằng chứng

Xem [ma trận Tuần 1–Tuần 2](TRACEABILITY-W1-W2.md) và [chỉ mục 29 ảnh AWS Tuần 2](evidence/week2/README.md). Số lượng 29 gồm 19 ảnh Quân và 10 ảnh Khôi.
