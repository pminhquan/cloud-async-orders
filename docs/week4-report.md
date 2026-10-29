# Báo cáo nghiệm thu Tuần 4

**Ngày nghiệm thu:** 29/10/2026, Asia/Bangkok (UTC+7).

**Môi trường:** AWS Academy Learner Lab của Quân, `us-east-1`, `LabRole`. Mã nguồn tham chiếu: `8b14e02ae64cc1a12e11d66c3f552824f67ab4b7`.

## 1. Phạm vi và phương pháp

Nghiệm thu gồm đối chiếu mã triển khai, luồng API Gateway → Producer → SQS → Consumer → DynamoDB, validation, replay/conflict, retry/DLQ và log/metrics. Request được gửi tuần tự với định danh riêng; item được đọc bằng `ConsistentRead=True`. Các phép thử trên AWS được phân biệt với unit tests dùng mô phỏng dịch vụ.

Số liệu Tuần 4 là bản ghi quan sát có chọn lọc từ phiên AWS thực tế; [chỉ mục minh chứng](evidence/week4/README.md) mô tả nguồn và giới hạn. Benchmark B1/B2/B3 và bằng chứng SNS/Alarm của Khôi thuộc ngày 24/10/2026, không phải thử nghiệm mới.

## 2. Trạng thái triển khai và hiệu chỉnh kỹ thuật

| Thành phần | Cấu hình/kết quả đối chiếu ngày 29/10 |
|---|---|
| `order-api` | HTTP API, `POST /orders` → `order-producer`, payload format `2.0`, authorization `NONE` |
| Producer và Consumer | Python 3.13, handler `lambda_function.lambda_handler`, memory 128 MB, timeout 3s, `LabRole` |
| Event Source Mapping | `ab1f7f06-157c-429b-bfcf-5cb15689f47f`, đúng `orders-queue` → `order-consumer`; sau hiệu chỉnh là Enabled, batch 1, window 0 |
| Queue chính | SQS Standard, visibility 60s, retention 345600s, SSE-SQS; redrive tới `orders-dlq`, `maxReceiveCount=5` |
| DLQ | Retention 1209600s, SSE-SQS; trước nghiệm thu có 2 message lịch sử |
| `Orders` | ACTIVE, partition key `orderId`, PAY_PER_REQUEST |
| CloudWatch | Có log groups Producer/Consumer; retention chưa đặt |
| Alarm/SNS của dự án trên Lab Quân | Không có trong inventory tại thời điểm đối chiếu |

Đối chiếu mã triển khai phát hiện Producer cũ thiếu `_validate`, không tương đương source tham chiếu. Sau khi lưu bản phục hồi, Producer được cập nhật từ source đã kiểm thử và kiểm tra lại hash. Consumer có AST tương đương source sau khi bỏ docstring nên không triển khai lại. Mapping được bật sau khi xác nhận đúng nguồn và queue trống; memory, timeout, role và target giữ nguyên.

| Định danh kiểm chứng Producer | Giá trị |
|---|---|
| SHA-256 source chuẩn hóa LF | `54d8014411164db8c43e7adee60867a1e6167be7ccbc00f103bffb7cba64bc1b` |
| Package CodeSha256 sau cập nhật | `mrUhf27ltD+maxXowCTR42HgkY8mE8TwPQZ8EuxPXHY=` |
| Trạng thái cập nhật | `Successful`, ghi nhận lúc 13:54:06 ngày 29/10 |

Kết quả cho thấy kiểm thử source cần kết hợp đối chiếu deployment thực tế để phát hiện sai lệch phiên bản.

## 3. Ma trận nghiệm thu trên AWS

Run `W4-20261029T065500Z` bắt đầu lúc 13:55:00 (`06:55:00 UTC`). Payload nền: `customerId=W4-20261029T065500Z`, `productId=P-W4-ACCEPTANCE`, `quantity=2`. Các request cách nhau tối thiểu 0,5s, không phải stress test.

| Mã | Dữ liệu/hành động | Kết quả quan sát | Đánh giá |
|---|---|---|---|
| T4-01 | POST payload hợp lệ | HTTP 202; orderId `e941e651-2be5-4a1e-9575-9bc47657967d`; đọc nhất quán mạnh xác nhận `PROCESSED` | Đạt |
| T4-02a | Body `{bad-json` | HTTP 400 | Đạt |
| T4-02b | Root JSON `[]` | HTTP 400 | Đạt |
| T4-03a–c | Bỏ lần lượt customerId, productId, quantity | 3/3 HTTP 400 | Đạt |
| T4-03d–e | customerId hoặc productId là whitespace | 2/2 HTTP 400 | Đạt |
| T4-04a–e | quantity: 0, -1, `"2"`, 1.5, true | 5/5 HTTP 400 | Đạt |
| T4-05 | Phát lại nguyên order có status `PENDING` qua SQS | Log `PROCESSED` theo messageId `469067fd-7f7e-47d2-a859-5197ab8dbc60`; item trước/sau giống nhau | Đạt |
| T4-06 | Direct Consumer invocation, cùng orderId nhưng quantity=99 | `FunctionError=Unhandled`, `ORDER_CONFLICT`; item trước/sau giống nhau | Đạt |
| T4-07 | Một sentinel invalid JSON qua queue chính | 5 log lỗi cùng messageId; sau đó queue chính trống và DLQ tăng 2 → 3 | Đạt trong phạm vi bằng chứng tương quan |

Tổng HTTP: **13/13 đúng kỳ vọng**, gồm 1 hợp lệ và 12 invalid. HTTP 202 xác nhận bước tiếp nhận; item `PROCESSED` cùng orderId xác nhận xử lý cuối. Nhánh invalid không gọi SQS được đối chiếu bằng thứ tự validation trong source và unit tests; không dùng riêng queue count xấp xỉ để kết luận không enqueue.

### Retry và DLQ

Sentinel có messageId `f0d75c4d-3739-45a3-a1e8-9fbedd75f7df`. CloudWatch ghi `INVALID_JSON` ở năm mốc UTC ngày 29/10/2026:

| Lần nhận/xử lý lỗi | Thời điểm UTC |
|---:|---|
| 1 | 06:56:55.770 |
| 2 | 06:57:55.790 |
| 3 | 06:58:55.809 |
| 4 | 06:59:55.810 |
| 5 | 07:00:55.830 |

Đây là năm lần nhận/xử lý lỗi tổng cộng, gồm lần đầu và bốn lần thử lại. Lúc 14:03:56 (`07:03:56 UTC`), queue chính là `0/0/0`, DLQ là `3/0/0`. Cấu hình redrive, log cùng messageId và biến đổi số lượng phù hợp với việc message mới chuyển DLQ. Không đọc body/messageId trực tiếp từ DLQ; không có thao tác Receive/Delete/Purge đối với hai message lịch sử.

## 4. Log, metrics và phạm vi monitoring

Collector dùng cửa sổ `06:54:30–07:04:00 UTC`, period 60s. Các giá trị dưới đây có trạng thái dữ liệu `OK`; dữ liệu thiếu không được tự thay bằng 0.

| Metric | Quan sát |
|---|---:|
| Producer Invocations / Errors / Throttles (Sum) | 13 / 0 / 0 |
| Consumer Invocations / Errors / Throttles (Sum) | 8 / 6 / 0 |
| ConcurrentExecutions Maximum, mỗi Lambda | 1 |
| Consumer Duration Maximum lớn nhất | 2574,54 ms |
| Queue chính NumberOfMessagesSent / Received / Deleted (Sum) | 3 / 7 / 2 |
| DLQ visible messages Maximum cuối cửa sổ | 3 |
| DLQ NumberOfMessagesReceived / Deleted (Sum) | 0 / 0 |

Sáu Errors của Consumer là lỗi dự kiến: một direct conflict và năm lần lỗi sentinel. Ba lần gửi SQS gồm đơn hợp lệ, replay và sentinel; hai lần xử lý thành công được đối chiếu với hai lần delete. Không throttling trong cửa sổ đo và concurrency tối đa 1 mỗi hàm không chứng minh năng lực toàn tài khoản hoặc tải production.

`NumberOfMessagesSent=0` trên DLQ không phủ định redrive, vì metric này không cộng message tự động chuyển vào DLQ; xem [định nghĩa metric SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-available-cloudwatch-metrics.html).

Lab Quân không có project alarm/topic trong inventory. [Minh chứng Lab Khôi ngày 24/10](week3-khoi-evidence.md) xác nhận subscription, publish/email và manual Alarm State → SNS → email. Kịch bản này kiểm chứng đường phân phối cảnh báo, chưa chứng minh DLQ metric tự kích hoạt email; không suy cấu hình giống nhau giữa hai Lab.

## 5. Đánh giá và quản lý tài nguyên

[Báo cáo cuối kỳ](final-report.md) phân tích dữ liệu B1/B2/B3: 60 message benchmark, 10 đơn load test và hai record cùng invocation. Mẫu nhỏ, client tuần tự và thời gian đối soát theo đợt giới hạn khả năng suy rộng. [Phân tích chi phí](week4-cost-analysis.md) trình bày sáu yếu tố dịch vụ và nguồn giá chính thức, không xem ngân sách Lab là hóa đơn hoặc công bố khoản tiết kiệm chưa đo.

Queue chính, DLQ, Orders, Lambda, API, mapping và log được giữ phục vụ đối soát. Hai queue benchmark rỗng được phân loại xem xét sau demo. Không xóa tài nguyên, purge DLQ hoặc rút retention trong đợt nghiệm thu. Kiểm tra lúc 15:42 ngày 29/10 ghi nhận Producer đúng hash, mapping Enabled, queue chính `0/0/0`, DLQ `3/0/0` và hai queue benchmark `0/0/0`.

## 6. Hồi quy và kết luận

[Kiểm thử offline](evidence/week4/offline-validation.md) đạt 56 tests/114 subtests, unittest 56, compileall, cfn-lint và bảy CLI checks. Mã nguồn ứng dụng, tests, scripts, IaC và CI tương đương nguồn tham chiếu; Tuần 4 tập trung nghiệm thu và tài liệu/minh chứng.

Các chức năng tiếp nhận, validation, xử lý bất đồng bộ và bảo vệ item khi replay/conflict đạt trong phạm vi thử nghiệm. Retry/DLQ có bằng chứng tương quan đúng cấu hình. Các giới hạn gồm API chưa có authorization, full-batch failure, mẫu tải nhỏ và monitoring khác nhau giữa hai môi trường. [Ma trận nghiệm thu](week4-execution.md) và [kịch bản demo](demo-script.md) tóm tắt cách đối chiếu kết quả.
