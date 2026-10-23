# Ma trận yêu cầu – phân công – kết quả – minh chứng (Tuần 1 và 2)

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Nhóm:** Phạm Minh Quân (24110311), Nguyễn Đoàn Minh Khôi (24110259)  
**AWS Region:** `us-east-1` · **Vai trò AWS:** `LabRole`

> **Cách đọc:** `PASS` chỉ đúng trong phạm vi test ghi ở cột “Đối soát”. Tuần 1 là PoC độc lập, không phải Full E2E. Lab Quân và Lab Khôi là hai môi trường khác nhau. Thời điểm đối chiếu GitHub: 17/10/2026.

## 1. Tuần 1 — nghiên cứu và PoC độc lập

| Yêu cầu | Thành viên | Trạng thái | Minh chứng gốc |
|---|---|---|---|
| Tạo SQS Standard `orders-queue` | Quân | Đã tạo PoC | [Ảnh queue](evidence/week1/sv1/week1-sqs-main-created.png) |
| Tạo `orders-dlq`, liên kết redrive | Quân | Đã tạo PoC | [DLQ](evidence/week1/sv1/week1-sqs-dlq-created.png), [redrive](evidence/week1/sv1/week1-sqs-dlq-linked.png) |
| Consumer Lambda xử lý message hợp lệ | Quân | PoC PASS | [Lambda](evidence/week1/sv1/week1-lambda-consumer-deployed.png), [test hợp lệ](evidence/week1/sv1/week1-lambda-valid-test-success.png) |
| Consumer lỗi → retry → DLQ | Quân | PoC PASS | [Log retry](evidence/week1/sv1/week1-sqs-lambda-retry-error-logs.png), [DLQ](evidence/week1/sv1/week1-sqs-dlq-message-arrived.png) |
| DynamoDB `Orders`, partition key `orderId` | Khôi | Đã tạo | [Bảng Orders](evidence/week1/sv2/01-dynamodb-orders.png) |
| Producer Lambda PoC | Khôi | HTTP 202; **chưa gửi SQS** | [Lambda 202](evidence/week1/sv2/02-lambda-producer-202.png) |
| API Gateway `POST /orders` | Khôi | HTTP 202 PoC | [API route](evidence/week1/sv2/03-api-route-post-orders.png), [PowerShell](evidence/week1/sv2/04-api-powershell-202.png) |
| SNS topic và email subscription | Khôi | Đã cấu hình | [SNS](evidence/week1/sv2/05-sns-topic.png), [subscription](evidence/week1/sv2/06-sns-email-confirmed.png) |
| Full E2E | Cả nhóm | **Chưa hoàn thành Tuần 1** | Mục tiêu Tuần 2 |

[Chi tiết Tuần 1](week1-report.md) · [Phân công](task-assignment.md)

## 2. Tuần 2 — tích hợp, kiểm thử và giới hạn bằng chứng

| Mã | Hạng mục | Phụ trách | Kết quả/đối soát | Minh chứng trực tiếp |
|---|---|---|---|---|
| W2-01 | Hợp đồng schema phẳng | Cả nhóm | Đã thống nhất | [Integration contract](integration-contract.md) |
| W2-02 | Producer gửi SQS | Khôi | PASS trên direct Lambda test; code đã merge | [Producer](../src/producer/lambda_function.py), [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7), [202](../screenshots/week2/khoi/01-producer-valid-202.png) |
| W2-03 | Validation đầu vào | Khôi | PASS trên direct Lambda test (`400` khi sai) | [Thiếu customerId](../screenshots/week2/khoi/02-producer-missing-customerid-400.png), [thiếu productId](../screenshots/week2/khoi/03-producer-missing-productid-400.png), [invalid JSON](../screenshots/week2/khoi/07-producer-invalid-json-400.png) |
| W2-04 | Invalid không enqueue | Khôi | PASS qua ảnh snapshot 8→8; đây là quan sát nhất thời | [Trước](../screenshots/week2/khoi/08-sqs-before-invalid-request.png), [400](../screenshots/week2/khoi/09-producer-invalid-request-400.png), [sau](../screenshots/week2/khoi/10-sqs-after-invalid-request.png) |
| W2-05 | Consumer ghi DynamoDB | Quân | PASS trên Lab Quân | [Consumer](../src/consumer/lambda_function.py), [DynamoDB](evidence/week2/W2-DynamoDB-Consumer-PROCESSED.png) |
| W2-06 | Idempotency | Quân | PASS qua replay cùng payload | [Replay](evidence/week2/W2-Consumer-Idempotency-Retry.png) |
| W2-07 | Conflict không overwrite | Quân | PASS | [ORDER_CONFLICT](evidence/week2/W2-Consumer-Order-Conflict-PASS.png), [item giữ nguyên](evidence/week2/W2-Consumer-Conflict-NoOverwrite.png) |
| W2-08 | Full E2E API tới DynamoDB | Quân và phối hợp | PASS trên Lab Quân, đối soát cùng orderId `e918c4af-3a9e-47c9-8a0c-13adbdfef82e` | [API 202](evidence/week2/W2-API-Gateway-POST-202.png), [DB PROCESSED](evidence/week2/W2-E2E-DynamoDB-PROCESSED.png) |
| W2-09 | Retry/DLQ | Quân | PASS trên Lab Quân, `maxReceiveCount=5` | [CloudWatch](evidence/week2/W2-Consumer-InvalidJSON-CloudWatch.png), [redrive](evidence/week2/W2-SQS-Redrive-MaxReceiveCount-5.png), [DLQ](evidence/week2/W2-DLQ-Invalid-Message-Verified.png) |
| W2-10 | Batch valid, mixed, replay | Quân | PASS **direct Lambda invocation**; chưa chứng minh tự gom SQS batch>1 | [Valid](evidence/week2/W2-Consumer-Batch-Valid-PASS.png), [mixed](evidence/week2/W2-Consumer-Batch-Mixed-Failure.png) |
| W2-11 | Small load 10 requests | Quân | PASS 10/10 trên Lab Quân; không phải stress test | [API](evidence/week2/W2-API-Small-Load-Test.png), [10 items](evidence/week2/W2-Small-Load-DynamoDB-PROCESSED.png) |
| W2-12 | Minh chứng và báo cáo | Cả nhóm | Bộ ảnh Quân 19, Khôi 10; tài liệu tổng hợp | [Index Tuần 2](evidence/week2/README.md), [Báo cáo](week2-report.md) |

### 3. Trạng thái source và Pull Request

- Consumer: [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5) — **Merged** vào `main`, commit `914de9b`.
- Producer: [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7) — **Merged** vào `main`, commit `015d420`.
- 19 ảnh AWS Quân bắt nguồn từ [PR #6](https://github.com/pminhquan/cloud-async-orders/pull/6); PR #6 vẫn **Open** tại thời điểm rà soát 17/10/2026.
- Tài liệu báo cáo và 10 ảnh Khôi ở [PR #8](https://github.com/pminhquan/cloud-async-orders/pull/8), hiện chưa merge.
- Không dùng mã hash của PR #8 để thay thế commit gốc của PR #5/#7.

### 4. Các mục không được nhận là PASS Tuần 2

- CloudWatch Alarm tự gửi SNS email khi DLQ có lỗi: dự kiến giai đoạn sau.
- Benchmark so sánh **Standard/FIFO** có số liệu thật: dự kiến giai đoạn sau.
- Stress test tải lớn và thống kê throughput/latency: chưa thực hiện.
- Triển khai IaC end-to-end: chưa xác minh.
- Full E2E trên **Lab Khôi**: không đủ bằng chứng đối soát một orderId qua API và DynamoDB, không bắt buộc phải lặp lại Lab Quân trừ khi giảng viên yêu cầu.
- Chạy lại toàn bộ test bằng Python ở máy Khôi tại thời điểm push: chưa thực hiện (máy báo không nhận Python).

### 5. Khai báo AI


[Chi tiết việc dùng AI](ai-declaration.md). Công cụ/model của từng thành viên phải do người đó xác nhận; không mặc định hai người dùng cùng model.
