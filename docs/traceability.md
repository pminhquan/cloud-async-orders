# Ma trận yêu cầu – phân công – kết quả – minh chứng (Bốn tuần)

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Nhóm:** Phạm Minh Quân (24110311), Nguyễn Đoàn Minh Khôi (24110259)  
**AWS Region:** `us-east-1` · **Vai trò AWS:** `LabRole`

> **Cách đọc:** `PASS` chỉ đúng trong phạm vi test ghi ở cột “Đối soát”. Các bảng Tuần 1–2 là kết quả lịch sử; Tuần 1 là PoC độc lập, không phải Full E2E. Hai Lab là hai môi trường khác nhau. Trạng thái PR được đối chiếu lại bằng public GitHub API ngày 29/10/2026; kết quả Tuần 3–4 nằm ở mục 6–7.

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
| W2-02 | Producer gửi SQS | Khôi | PASS trên direct Lambda test; code đã merge | [Producer](../src/producer/lambda_function.py), [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7), [202](evidence/week2/khoi/01-producer-valid-202.png) |
| W2-03 | Validation đầu vào | Khôi | PASS trên direct Lambda test (`400` khi sai) | [Thiếu customerId](evidence/week2/khoi/02-producer-missing-customerid-400.png), [thiếu productId](evidence/week2/khoi/03-producer-missing-productid-400.png), [invalid JSON](evidence/week2/khoi/07-producer-invalid-json-400.png) |
| W2-04 | Invalid không enqueue | Khôi | PASS qua ảnh snapshot 8→8; đây là quan sát nhất thời | [Trước](evidence/week2/khoi/08-sqs-before-invalid-request.png), [400](evidence/week2/khoi/09-producer-invalid-request-400.png), [sau](evidence/week2/khoi/10-sqs-after-invalid-request.png) |
| W2-05 | Consumer ghi DynamoDB | Quân | PASS trên Lab Quân | [Consumer](../src/consumer/lambda_function.py), [DynamoDB](evidence/week2/W2-DynamoDB-Consumer-PROCESSED.png) |
| W2-06 | Idempotency | Quân | PASS qua replay cùng payload | [Replay](evidence/week2/W2-Consumer-Idempotency-Retry.png) |
| W2-07 | Conflict không overwrite | Quân | PASS | [ORDER_CONFLICT](evidence/week2/W2-Consumer-Order-Conflict-PASS.png), [item giữ nguyên](evidence/week2/W2-Consumer-Conflict-NoOverwrite.png) |
| W2-08 | Full E2E API tới DynamoDB | Quân và phối hợp | PASS trên Lab Quân, đối soát cùng orderId `e918c4af-3a9e-47c9-8a0c-13adbdfef82e` | [API 202](evidence/week2/W2-API-Gateway-POST-202.png), [DB PROCESSED](evidence/week2/W2-E2E-DynamoDB-PROCESSED.png) |
| W2-09 | Retry/DLQ | Quân | PASS trên Lab Quân, `maxReceiveCount=5` | [CloudWatch](evidence/week2/W2-Consumer-InvalidJSON-CloudWatch.png), [redrive](evidence/week2/W2-SQS-Redrive-MaxReceiveCount-5.png), [DLQ](evidence/week2/W2-DLQ-Invalid-Message-Verified.png) |
| W2-10 | Batch valid, mixed, replay | Quân | PASS **direct Lambda invocation**; chưa chứng minh tự gom SQS batch>1 | [Valid](evidence/week2/W2-Consumer-Batch-Valid-PASS.png), [mixed](evidence/week2/W2-Consumer-Batch-Mixed-Failure.png) |
| W2-11 | Small load 10 requests | Quân | PASS 10/10 trên Lab Quân; không phải stress test | [API](evidence/week2/W2-API-Small-Load-Test.png), [10 items](evidence/week2/W2-Small-Load-DynamoDB-PROCESSED.png) |
| W2-12 | Minh chứng và báo cáo | Cả nhóm | Bộ ảnh Quân 19, Khôi 10; tài liệu tổng hợp | [Index Tuần 2](evidence/week2/README.md), [Báo cáo](week2-report.md) |
| W2-13 | Nhật ký theo yêu cầu tối thiểu 8 giờ/người | Mỗi người | Quản lý riêng trong nhật ký học phần | [Tuần 1](worklog/week1.md), [Tuần 2](worklog/week2.md) |

### 3. Trạng thái source và Pull Request

- Consumer: [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5) — **Merged** vào `main`, commit `914de9b`.
- Producer: [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7) — **Merged** vào `main`, commit `015d420`.
- 19 ảnh AWS Quân bắt nguồn từ [PR #6](https://github.com/pminhquan/cloud-async-orders/pull/6); PR #6 hiện **Closed, không merge**. Bộ ảnh đã có trong phần tổng hợp, không dùng trạng thái PR này để phủ nhận tệp đã tích hợp.
- Tài liệu và 10 ảnh Khôi ở [PR #8](https://github.com/pminhquan/cloud-async-orders/pull/8), đã merge; [PR #9](https://github.com/pminhquan/cloud-async-orders/pull/9) cũng đã merge.
- Không dùng mã hash của PR #8 để thay thế commit gốc của PR #5/#7.

### 4. Các mục không được nhận là PASS Tuần 2

- CloudWatch Alarm tự gửi SNS email khi DLQ có lỗi: dự kiến giai đoạn sau.
- Benchmark so sánh **Standard/FIFO** có số liệu thật: dự kiến giai đoạn sau.
- Stress test tải lớn và thống kê throughput/latency: chưa thực hiện.
- Triển khai IaC end-to-end: chưa xác minh.
- Full E2E trên **Lab Khôi**: không đủ bằng chứng đối soát một orderId qua API và DynamoDB, không bắt buộc phải lặp lại Lab Quân trừ khi giảng viên yêu cầu.

### 5. Nhật ký học phần và khai báo công cụ

Nhật ký thời lượng được quản lý riêng theo [yêu cầu dự án](requirements.md). [Khai báo AI](ai-declaration.md) ghi công cụ, phạm vi hỗ trợ và trách nhiệm xác nhận của từng thành viên.

## 6. Tuần 3 — dữ liệu thực nghiệm ngày 24/10/2026

| Yêu cầu | Kết quả và giới hạn | Minh chứng |
|---|---|---|
| Monitoring IaC, collector và CI | Template/gate offline PASS; không tự suy thành triển khai cả hai Lab | [Template](../iac/week3-monitoring.yaml), [báo cáo](week3-report.md) |
| Standard/FIFO B1 | Ba kịch bản × 20 message gửi/nhận đủ; client tuần tự, không stress test | [B1](week3-quan-b1-results.md) |
| Load B2 | 10/10 HTTP 202 và PROCESSED; 3,5846s là đợt đối soát sau gửi | [JSON B2](evidence/week3/quan/b2-2026-10-24/load/load-test-summary.json) |
| Batch thật B3 | Hai record cùng Lambda RequestId | [Batch proof](evidence/week3/quan/b3-2026-10-24/batch-proof.json) |
| SNS/Alarm Khôi | Email và manual Alarm State, chưa chứng minh DLQ metric tự kích hoạt | [Phạm vi Khôi](week3-khoi-evidence.md) |
| PR #11–#15 | Đã merge; main ở 8b14e02 khi đối chiếu 29/10 | [CI đúng main](https://github.com/pminhquan/cloud-async-orders/actions/runs/40163636601) |

## 7. Tuần 4 — nghiệm thu ngày 29–30/10/2026

| Mã | Kết quả và phạm vi | Minh chứng |
|---|---|---|
| W4-01 | Inventory thật Lab Quân; giữ phân biệt hai môi trường | [Inventory](week4-report.md) |
| W4-02 | Producer đúng main, ESM Enabled, API 202 và đúng orderId PROCESSED | [Deployment/E2E](week4-report.md) |
| W4-03 | 13/13 HTTP đúng kỳ vọng; replay/conflict giữ item; 5 lần nhận/lỗi và biến đổi queue/DLQ tương ứng | [Ma trận và giới hạn DLQ](week4-report.md) |
| W4-04 | Lab Quân ngày 30/10: metric DLQ → ALARM → SNS → email khớp; subscription confirmed trước khi tạo alarm | [Monitoring](week4-report.md#71-kết-quả-sau-cập-nhật-đã-được-phê-duyệt) |
| W4-05 | Phân tích B1/B2/B3 bằng dữ liệu có sẵn, không suy năng lực production | [Hiệu năng](week4-report.md#51-hiệu-năng-từ-minh-chứng-hiện-có) |
| W4-06 | Mô hình chi phí và nguồn chính thức; không bịa hóa đơn | [Chi phí](week4-cost-analysis.md) |
| W4-07 | KEEP/REVIEW, kiểm tra trạng thái cuối, không purge/delete | [Tài nguyên](week4-report.md) |
| W4-08 | Hồi quy offline đạt; phân biệt source tham chiếu và head CI của từng PR | [Kiểm thử](evidence/week4/offline-validation.md), [hồ sơ](SUBMISSION.md) |
| W4-09 | Báo cáo từng tuần, đánh giá kỹ thuật và kịch bản 9:20 | [Nghiệm thu Tuần 4](week4-report.md), [demo](demo-script.md) |

Kết quả ngày 29/10 được bổ sung JSON AWS và ảnh gốc ngày 30/10. [Nguồn minh chứng](evidence/week4/README.md) phân biệt giới hạn redrive, monitoring thủ công/metric-driven và từng Lab.
