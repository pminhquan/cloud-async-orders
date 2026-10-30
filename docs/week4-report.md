# Báo cáo nghiệm thu Tuần 4

**Ngày nghiệm thu:** 29–30/10/2026, Asia/Bangkok (UTC+7).

**Môi trường:** AWS Academy Learner Lab của Quân, `us-east-1`, `LabRole`. Mã nguồn tham chiếu: `8b14e02ae64cc1a12e11d66c3f552824f67ab4b7`.

## 1. Phạm vi và phương pháp

Nghiệm thu gồm đối chiếu mã triển khai, luồng API Gateway → Producer → SQS → Consumer → DynamoDB, validation, replay/conflict, retry/DLQ và log/metrics. Request được gửi tuần tự với định danh riêng; item được đọc bằng `ConsistentRead=True`. Các phép thử trên AWS được phân biệt với unit tests dùng mô phỏng dịch vụ.

Kết quả ngày 29/10 là bản ghi quan sát; ngày 30/10 bổ sung JSON AWS và ảnh gốc tại [chỉ mục minh chứng](evidence/week4/README.md). Benchmark B1/B2/B3 và bằng chứng SNS/Alarm của Khôi thuộc ngày 24/10/2026, không phải thử nghiệm mới.

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

Inventory ngày 29/10 trên Lab Quân chưa có project alarm/topic. [Minh chứng Lab Khôi ngày 24/10](week3-khoi-evidence.md) thuộc phép thử manual Alarm State → SNS → email. Chuỗi metric-driven trên Lab Quân được kiểm chứng riêng ngày 30/10 tại mục 7.1.

## 5. Đánh giá và quản lý tài nguyên

[Phân tích chi phí](week4-cost-analysis.md) trình bày sáu yếu tố dịch vụ và nguồn giá chính thức, không xem ngân sách Lab là hóa đơn hoặc công bố khoản tiết kiệm chưa đo.

Queue chính, DLQ, Orders, Lambda, API, mapping và log được giữ phục vụ đối soát. Hai queue benchmark rỗng được phân loại xem xét sau demo. Không xóa tài nguyên, purge DLQ hoặc rút retention trong đợt nghiệm thu. Kiểm tra lúc 15:42 ngày 29/10 ghi nhận Producer đúng hash, mapping Enabled, queue chính `0/0/0`, DLQ `3/0/0` và hai queue benchmark `0/0/0`.

### 5.1. Hiệu năng từ minh chứng hiện có

Tái sử dụng dữ liệu AWS ngày **24/10/2026**, không chạy lại benchmark. B1 đo SQS API độc lập bằng client tuần tự, `batchSize=1`, 20 message mỗi kịch bản, không có Consumer tham gia. Dấu chấm trong bảng là dấu thập phân.

| Kịch bản B1 | Gửi/nhận đủ | Send throughput (msg/s) | Median send (ms) | P95 send (ms) |
|---|---:|---:|---:|---:|
| [Standard](evidence/week3/quan/b1-2026-10-24/standard/benchmark-summary.json) | 20/20 | 2.880 | 243.891 | 260.606 |
| [FIFO, 1 group](evidence/week3/quan/b1-2026-10-24/fifo-single/benchmark-summary.json) | 20/20 | 2.734 | 246.461 | 254.454 |
| [FIFO, 5 groups](evidence/week3/quan/b1-2026-10-24/fifo-multi/benchmark-summary.json) | 20/20 | 2.007 | 298.031 | 957.534 |

Không thấy duplicate trong mẫu; Standard có sai thứ tự, FIFO giữ thứ tự trong từng group ở lần chạy này. Client tuần tự và đường truyền giới hạn phép đo; 2–3 msg/s không phải trần SQS và một lần chạy không chứng minh FIFO nhiều group chậm hơn nói chung. [Phân tích B1](week3-quan-b1-results.md) giữ đầy đủ điều kiện và provenance.

[B2](evidence/week3/quan/b2-2026-10-24/load/load-test-summary.json) có 10/10 HTTP 202 và 10/10 `PROCESSED`; API mean/median/P95 lần lượt `931.091 / 824.446 / 1798.399 ms`. Đợt đối soát sau gửi mất `3.5846s`, không phải latency E2E từng đơn. [B3](evidence/week3/quan/b3-2026-10-24/batch-proof.json) chứng minh hai record cùng RequestId `669f8c38-d85a-55dd-9a5a-ef6e0015632a`: duration `2784.26 ms`, billed `3139 ms`, memory `128 MB`, max used `90 MB`, init `354.04 ms`.

Mẫu nhỏ không đủ căn cứ đổi Standard/FIFO, memory, timeout, batch hoặc concurrency. Duration tối đa Tuần 4 `2574.54 ms` ở timeout `3s` chỉ là quan sát trong cửa sổ nhỏ, chưa xác định timeout an toàn cho mọi tải. Batch có thể giảm invocation nhưng full-batch failure làm phát lại cả record đã xử lý; cần số đo so sánh trước khi đổi cấu hình.

Rà soát nguồn giá ngày 30/10: [SQS](https://aws.amazon.com/sqs/pricing/), [Lambda](https://aws.amazon.com/lambda/pricing/), [DynamoDB](https://aws.amazon.com/dynamodb/pricing/), [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/), [API Gateway](https://aws.amazon.com/api-gateway/pricing/) và [SNS](https://aws.amazon.com/sns/pricing/). Giữ mô hình trong tài liệu chi phí; chưa có billing export của Lab nên chưa tính tổng tiền hoặc mức tiết kiệm. Riêng invocation B3 có phần compute `128/1024 × 3.139 = 0.392375 GB-s`, không đại diện chi phí toàn pipeline.

## 6. Hồi quy và kết luận

[Kiểm thử offline](evidence/week4/offline-validation.md) đạt 56 tests/114 subtests, unittest 56, compileall, cfn-lint và bảy CLI checks. Mã nguồn ứng dụng, tests, scripts, IaC và CI tương đương nguồn tham chiếu; Tuần 4 tập trung nghiệm thu và tài liệu/minh chứng.

Các chức năng tiếp nhận, validation, xử lý bất đồng bộ và bảo vệ item khi replay/conflict đạt trong phạm vi thử nghiệm. Retry/DLQ có bằng chứng tương quan đúng cấu hình. Các giới hạn gồm API chưa có authorization, full-batch failure, mẫu tải nhỏ và monitoring khác nhau giữa hai môi trường. [Ma trận nghiệm thu](week4-execution.md) và [kịch bản demo](demo-script.md) tóm tắt cách đối chiếu kết quả.

## 7. Rà soát bổ sung ngày 30/10/2026

Kiểm kê chỉ đọc tại `14:14–14:18 UTC` (`21:14–21:18 UTC+7`), Lab Quân, `us-east-1`. [JSON AWS thực tế](evidence/week4/quan/aws-current-state-2026-10-30.json) chứa cấu hình, log và datapoints; [ảnh cấu hình](evidence/week4/quan/W4-AWS-Configuration.jpg), [ảnh retry/Orders](evidence/week4/quan/W4-Retry-DynamoDB.jpg) giữ nguyên khung hình, Account ID và email. Các mục 2–4 giữ kết quả lịch sử ngày 29/10.

| Thành phần | Kiểm kê trước cập nhật ngày 30/10 |
|---|---|
| Lambda | Cả hai Active/Successful, Python 3.13, 128 MB, timeout 3s, LabRole; target đúng queue/bảng. Producer khớp hash LF; Consumer khác hash nhưng AST bỏ docstring khớp repo, không triển khai lại. |
| SQS | Queue chính `0/0/0`, visibility 60s, redrive `maxReceiveCount=5`; DLQ `1/0/0`, retention 14 ngày. Nguyên nhân giảm từ 3 xuống 1 chưa xác minh. |
| ESM | `order-consumer` **Disabled**, batch 1/window 0, maximum concurrency 5, LastModified `2026-10-29T16:46:47Z`, lý do `USER_INITIATED`. Mapping legacy `order-processor` cũng Disabled. CloudTrail lookup trong cửa sổ từ 29/10 không trả event tương ứng; chủ đích thay đổi chưa xác định. |
| DynamoDB/API | Orders ACTIVE, khóa `orderId` kiểu String, PAY_PER_REQUEST; đơn nghiệm thu cũ vẫn PROCESSED. HTTP API `POST /orders` → Producer, payload 2.0, stage `$default` DEPLOYED/AutoDeploy; không gửi POST mới. |
| Monitoring | Không có metric alarm trong kết quả `DescribeAlarms`, không có topic `order-dlq-alert`. DLQ visible Maximum=1 ở 15 datapoints `13:59–14:14 UTC`; chưa có chuỗi metric-driven Alarm → SNS → Email. |

Đã xuất lại đủ năm log `INVALID_JSON` cùng sentinel messageId, phân trang hoàn tất; Producer log PENDING và hai Consumer log PROCESSED khớp order lịch sử. Metrics cửa sổ nghiệm thu khớp số liệu mục 4. Chưa đọc message trong DLQ nên chỉ giữ kết luận tương quan redrive. Không chạy lại E2E, benchmark, tải hoặc tạo message.

### 7.1. Kết quả sau cập nhật đã được phê duyệt

- Mapping `order-consumer` đã **Enabled** sau khi xác nhận queue chính rỗng; giữ batch 1/window 0/maximum concurrency 5. Mapping legacy giữ Disabled; code và cấu hình hai Lambda không đổi.
- SNS topic `order-dlq-alert` và subscription email đã tạo; xác nhận subscription trước khi triển khai alarm. Policy bổ sung chỉ cho phép đúng alarm CloudWatch của tài khoản publish vào topic.
- Stack `cloud-async-orders-week4-monitoring` đạt **CREATE_COMPLETE**, chỉ chứa **một alarm DLQ** từ [template hiện có](../iac/week3-monitoring.yaml): `Maximum >= 1`, period 60s, evaluation 1, `TreatMissingData=notBreaching`; alarm Consumer/backlog tắt. Template gửi SNS cho cả ALARM và OK.
- Datapoint `1.0` lúc `14:33:00 UTC` làm alarm chuyển `INSUFFICIENT_DATA → ALARM` lúc `14:35:15.461 UTC`; SNS action thành công lúc `14:35:15.508 UTC`. Email nhận được khớp alarm, Region, Account ID, metric và timestamp `14:35:15 UTC` (`21:35:15 UTC+7`). Đã kiểm chứng **DLQ metric → CloudWatch Alarm → SNS → Email** bằng metric thực tế.

Minh chứng: [JSON cấu hình/kết quả/history](evidence/week4/quan/monitoring-2026-10-30.json), [ảnh CloudWatch Console](evidence/week4/quan/W4-Metric-Alarm.jpg), [ảnh email gốc](evidence/week4/quan/W4-SNS-Email.png). Ảnh email do sinh viên cung cấp được lưu nguyên byte; phần người nhận hiển thị “to me”, địa chỉ subscription được xác minh riêng qua SNS. Trạng thái cuối ghi nhận queue chính `0/0/0`, DLQ `1/0/0`; alarm ALARM đúng ngưỡng. Dùng message DLQ đã có, không tạo thêm lỗi, ép trạng thái alarm hoặc xóa tài nguyên.
