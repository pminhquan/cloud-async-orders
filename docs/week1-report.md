# BÁO CÁO TIẾN ĐỘ TUẦN 1

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Môn học:** CLC0332779_05UTExMC - Điện toán đám mây  
**GVHD:** TS. Huỳnh Xuân Phụng  
**Region:** `us-east-1`

## 1. Thành viên

| MSSV | Họ tên |
|---|---|
| 24110311 | Phạm Minh Quân |
| 24110259 | Nguyễn Đoàn Minh Khôi |

## 2. Mục tiêu Tuần 1

- Hiểu các dịch vụ Serverless chính.
- Xác định kiến trúc Producer–Queue–Consumer.
- Dựng PoC từng phía.
- Kiểm thử SQS/DLQ/Consumer riêng.
- Kiểm thử API/Producer/DynamoDB/SNS riêng.
- Chuẩn bị repository, evidence và tài liệu cho Tuần 2.

## 3. Phần Phạm Minh Quân

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

## 9. Khai báo sử dụng AI

Phần hỗ trợ AI của hai thành viên được khai báo tập trung tại [ai-declaration.md](ai-declaration.md). Nhóm trực tiếp triển khai, kiểm thử và chụp minh chứng trên AWS Learner Lab.

## 10. Kết luận

Tuần 1 hoàn thành nền tảng và hai PoC độc lập. Producer chưa gửi SQS thật và Consumer chưa ghi DynamoDB. Full E2E được chuyển sang Tuần 2.
