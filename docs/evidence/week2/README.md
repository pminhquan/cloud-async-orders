# Minh chứng AWS Tuần 2 — chỉ mục có liên kết trực tiếp

Bộ ảnh gốc của Quân bắt nguồn từ PR #6 (đã Closed, không merge) và được đưa vào `main` qua PR #8; ảnh nằm **trực tiếp** tại thư mục này. Phạm vi kiểm thử tại hai Lab được phân biệt rõ; không suy đoán AWS Lab Khôi đạt E2E từ Lab Quân.

## A. Bộ 19 ảnh Phạm Minh Quân (Lab tích hợp chính)

| STT | Tệp minh chứng | Diễn giải |
|---:|---|---|
| 01 | [W2-API-Gateway-POST-202.png](W2-API-Gateway-POST-202.png) | Ảnh kiểm thử AWS Lab Quân |
| 02 | [W2-API-Small-Load-Test.png](W2-API-Small-Load-Test.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 03 | [W2-Consumer-Batch-Mixed-Failure.png](W2-Consumer-Batch-Mixed-Failure.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 04 | [W2-Consumer-Batch-Valid-PASS.png](W2-Consumer-Batch-Valid-PASS.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 05 | [W2-Consumer-Conflict-NoOverwrite.png](W2-Consumer-Conflict-NoOverwrite.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 06 | [W2-Consumer-Direct-Test-PASS.png](W2-Consumer-Direct-Test-PASS.png) | Ảnh kiểm thử AWS Lab Quân |
| 07 | [W2-Consumer-Idempotency-Retry.png](W2-Consumer-Idempotency-Retry.png) | Ảnh kiểm thử AWS Lab Quân |
| 08 | [W2-Consumer-InvalidJSON-CloudWatch.png](W2-Consumer-InvalidJSON-CloudWatch.png) | Ảnh kiểm thử AWS Lab Quân |
| 09 | [W2-Consumer-Order-Conflict-PASS.png](W2-Consumer-Order-Conflict-PASS.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 10 | [W2-Consumer-SQS-Trigger-Enabled.png](W2-Consumer-SQS-Trigger-Enabled.png) | Ảnh kiểm thử AWS Lab Quân |
| 11 | [W2-DLQ-Invalid-Message-Verified.png](W2-DLQ-Invalid-Message-Verified.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 12 | [W2-DynamoDB-Consumer-PROCESSED.png](W2-DynamoDB-Consumer-PROCESSED.png) | Ảnh kiểm thử AWS Lab Quân |
| 13 | [W2-DynamoDB-Orders-Active.png](W2-DynamoDB-Orders-Active.png) | Ảnh kiểm thử AWS Lab Quân |
| 14 | [W2-E2E-DynamoDB-PROCESSED.png](W2-E2E-DynamoDB-PROCESSED.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 15 | [W2-Producer-Direct-Test-PASS.png](W2-Producer-Direct-Test-PASS.png) | Ảnh kiểm thử AWS Lab Quân |
| 16 | [W2-Producer-SQS-Message-Received.png](W2-Producer-SQS-Message-Received.png) | Ảnh kiểm thử AWS Lab Quân |
| 17 | [W2-SQS-Redrive-MaxReceiveCount-5.png](W2-SQS-Redrive-MaxReceiveCount-5.png) | Ảnh kiểm thử AWS Lab Quân |
| 18 | [W2-SQS-Retry-DLQ-Counts.png](W2-SQS-Retry-DLQ-Counts.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |
| 19 | [W2-Small-Load-DynamoDB-PROCESSED.png](W2-Small-Load-DynamoDB-PROCESSED.png) | Minh chứng tích hợp, DLQ, conflict, batch hoặc load Lab Quân |

**Các mốc đối soát:** `orderId=e918c4af-3a9e-47c9-8a0c-13adbdfef82e` ở E2E; `status=PROCESSED` trong DynamoDB; `INVALID_JSON` khi xử lý message lỗi; `maxReceiveCount=5` trong redrive. Batch nhiều record là *direct Lambda invocation*, còn trigger SQS thực tế đã dùng batch size `1`, window `0`, concurrency `5` trong bài test Lab Quân.

## B. Bộ 10 ảnh Nguyễn Đoàn Minh Khôi (Producer validation)

| STT | Ảnh | Ý nghĩa |
|---:|---|---|
| 01 | [Valid → 202](khoi/01-producer-valid-202.png) | Producer direct test hợp lệ |
| 02 | [Thiếu customerId](khoi/02-producer-missing-customerid-400.png) | 400 |
| 03 | [Thiếu productId](khoi/03-producer-missing-productid-400.png) | 400 |
| 04 | [Invalid quantity A](khoi/04-producer-invalid-quantity-400-a.png) | 400 |
| 05 | [Invalid quantity B](khoi/05-producer-invalid-quantity-400-b.png) | 400 |
| 06 | [Invalid quantity C](khoi/06-producer-invalid-quantity-400-c.png) | 400 |
| 07 | [Malformed JSON](khoi/07-producer-invalid-json-400.png) | 400 |
| 08 | [SQS trước invalid](khoi/08-sqs-before-invalid-request.png) | 8 available, 0 in flight |
| 09 | [Invalid request 400](khoi/09-producer-invalid-request-400.png) | request không hợp lệ |
| 10 | [SQS sau invalid](khoi/10-sqs-after-invalid-request.png) | vẫn 8 available, 0 in flight |

**Lưu ý:** số liệu hàng đợi trước/sau là snapshot, không thay thế unit test mock xác nhận không gọi `send_message`. Các ảnh Khôi là Lambda Test, không phải API Gateway E2E cùng orderId.

## C. Nguồn và liên kết

- [Báo cáo Tuần 2](../../week2-report.md)
- [Ma trận đối chiếu yêu cầu](../../traceability.md)
- [PR #6 — nguồn gốc 19 ảnh](https://github.com/pminhquan/cloud-async-orders/pull/6)
- [PR #8 — nhánh báo cáo](https://github.com/pminhquan/cloud-async-orders/pull/8)
