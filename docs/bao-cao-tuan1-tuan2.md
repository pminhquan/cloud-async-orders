# BÁO CÁO TIẾN ĐỘ DỰ ÁN — TUẦN 1 VÀ TUẦN 2

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Môn học:** CLC0332779_05UTExMC - Điện toán đám mây  
**GVHD:** TS. Huỳnh Xuân Phụng  
**Nhóm:** Serverless  
**Region:** `us-east-1`

## Thành viên

| MSSV | Họ tên |
|---|---|
| 24110311 | Phạm Minh Quân |
| 24110259 | Nguyễn Đoàn Minh Khôi |

---

## Tóm tắt tiến độ

| Tuần | Trọng tâm | Kết quả chính |
|---|---|---|
| Tuần 1 | Nghiên cứu + PoC riêng từng phía | SQS/DLQ/Consumer PoC và API/Producer/DynamoDB/SNS PoC hoàn thành; chưa Full E2E |
| Tuần 2 | Tích hợp + validation + idempotency + retry/DLQ | Full E2E PASS trên Lab Quân; Producer validation PASS trên Lab Khôi; idempotency/conflict/retry-DLQ/batch/load nhỏ PASS |

---

## PHẦN A — TUẦN 1

### 1. Mục tiêu Tuần 1

- Hiểu các dịch vụ Serverless chính.
- Xác định kiến trúc Producer–Queue–Consumer.
- Dựng PoC từng phía.
- Kiểm thử SQS/DLQ/Consumer riêng.
- Kiểm thử API/Producer/DynamoDB/SNS riêng.
- Chuẩn bị repository, evidence và tài liệu cho Tuần 2.

## 2. Phần Phạm Minh Quân

- Tạo `orders-queue`.
- Tạo `orders-dlq`.
- Liên kết redrive.
- Tạo Consumer Lambda PoC.
- Test valid message.
- Test invalid message.
- Quan sát retry.
- Xác nhận message lỗi đi DLQ.
- Nghiên cứu Standard/FIFO.
- Chuẩn bị sơ đồ kiến trúc.
- Thu thập 26 ảnh AWS SV1 trong bộ evidence Tuần 1.

## 4. Phần Nguyễn Đoàn Minh Khôi

- Tạo DynamoDB `Orders`.
- Partition key `orderId`.
- Capacity mode On-demand.
- Tạo `order-producer` PoC.
- Tạo `order-api`.
- Route `POST /orders`.
- Test Lambda Producer trả `202`.
- Test API PowerShell trả `202`.
- Tạo SNS `order-dlq-alert`.
- Xác nhận email subscription.
- Thu thập 6 ảnh AWS SV2.

## 5. Kiến trúc Tuần 1

```text
Khôi: API Gateway → Producer PoC
Quân: SQS → Consumer PoC
       SQS → DLQ
DynamoDB/SNS được tạo riêng
```

Full E2E chưa hoàn thành trong Tuần 1.

## 6. Mức độ hoàn thành

| Hạng mục | Kết quả |
|---|---|
| Nghiên cứu dịch vụ | 100% |
| Kiến trúc | 100% |
| SQS/DLQ/Consumer PoC | Hoàn thành PoC |
| API/Producer PoC | Hoàn thành PoC |
| DynamoDB | Đã tạo |
| SNS | Đã tạo/confirmed |
| Full E2E | Chưa làm, chuyển Tuần 2 |

## 7. Evidence

- [Chỉ mục evidence Tuần 1](evidence/week1/README.md)
- [Worklog Tuần 1](worklog/week1.md)
- [Kiến trúc](architecture/README.md)
- [AWS Inventory](aws-inventory.md)

## 8. GitHub/commit Tuần 1

Các commit/nhánh Tuần 1 đã từng sử dụng:

```text
ff64af9  SQS/DLQ/Consumer và kiểm thử Tuần 1
76f0ec3  Producer/API/DynamoDB/SNS và minh chứng Tuần 1
a0df3e9  Tổng hợp báo cáo/kiến trúc/minh chứng
9d9ea4b  Sửa link minh chứng và khai báo AI
```

Nhánh evidence:

```text
week1-full-evidence
```

## 9. AI hỗ trợ

ChatGPT được sử dụng để:
- giải thích dịch vụ/kiến trúc;
- gợi ý Lambda PoC;
- gợi ý JSON test và PowerShell;
- hỗ trợ troubleshooting;
- hỗ trợ tổ chức tài liệu.

Nhóm trực tiếp triển khai, kiểm thử và chụp evidence trên AWS Learner Lab.

## 10. Kết luận

Tuần 1 hoàn thành nền tảng và hai PoC độc lập. Producer chưa gửi SQS thật và Consumer chưa ghi DynamoDB. Full E2E được chuyển sang Tuần 2.

---

## PHẦN B — TUẦN 2

### 1. Mục tiêu Tuần 2

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

Theo thông tin nhóm cung cấp, **Phạm Minh Quân sử dụng ChatGPT / GPT-6.0** để tham khảo xử lý Consumer/SQS, DynamoDB conditional write, idempotency, `ORDER_CONFLICT`, retry/DLQ, batch/replay, E2E và tests. Các nhóm nội dung yêu cầu AI và kết quả gợi ý đã được tổng hợp tại [docs/ai-declaration.md](ai-declaration.md); đây không phải bản chép lịch sử prompt nguyên văn.

Nhóm trực tiếp triển khai, kiểm thử và xác nhận kết quả thực tế.

## 9. Worklog

Xem [worklog/week2.md](worklog/week2.md).

**Xác nhận của nhóm:** người nộp báo cáo cả hai đã đạt mức tối thiểu 8 giờ/người; hiện không có số giờ/ngày chi tiết để kiểm toán. Xem worklog, chỉ điền giờ chi tiết khi có dữ liệu thật.

## 10. Kết luận

Tuần 2 đã đạt mục tiêu tích hợp lõi. Producer, SQS, Consumer và DynamoDB đã hoạt động theo pipeline bất đồng bộ; validation, idempotency và DLQ đã được kiểm thử. Các phần CloudWatch Alarm/SNS alert hoàn chỉnh, benchmark Standard/FIFO và load lớn được chuyển sang tuần sau.

---

## PHẦN C — CHECKLIST CHỐT NỘP

- [x] Source Producer/Consumer.
- [x] Unit tests hiện tại: `33 passed, 81 subtests passed`.
- [x] Evidence Tuần 1.
- [x] Evidence Producer Tuần 2 phía Khôi.
- [x] Evidence Tuần 2 phía Quân đã được báo cáo/push qua PR tài liệu.
- [ ] Điền giờ làm thực tế Tuần 1 và Tuần 2.
- [x] Phần AI của Quân đã được tổng hợp theo thông tin nhóm cung cấp (ChatGPT / GPT-6.0); xem [khai báo chi tiết](ai-declaration.md).
- [ ] Kiểm tra trạng thái PR #6 và toàn bộ link sau push cuối.


## Đối chiếu yêu cầu theo người thực hiện và bằng chứng

Xem [ma trận Tuần 1–Tuần 2](TRACEABILITY-W1-W2.md) và [chỉ mục 29 ảnh AWS Tuần 2](evidence/week2/README.md). Số lượng 29 gồm 19 ảnh Quân và 10 ảnh Khôi.
