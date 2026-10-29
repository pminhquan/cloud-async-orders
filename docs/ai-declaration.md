# Khai báo sử dụng AI — Bốn tuần

> Các mục 1–5 là khai báo lịch sử Tuần 1–2 theo thông tin nhóm cung cấp. Phần Tuần 3–4 được bổ sung riêng bên dưới, không sửa thành tích hoặc lịch sử model của từng thành viên.

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda\
**Môn học:** CLC0332779_05UTExMC – Điện toán đám mây\
**Nhóm:** Serverless

## 1. Công cụ và thông tin theo thành viên

| Thành viên | Công cụ AI | Model khai báo | Phần việc được hỗ trợ | Trạng thái |
|---|---|---|---|---|
| Nguyễn Đoàn Minh Khôi (24110259) | ChatGPT | GPT-5.6 Sol | Producer Lambda, API Gateway, SQS, input validation, xử lý lỗi AWS, thu thập minh chứng và báo cáo | Đã tổng hợp |
| Phạm Minh Quân (24110311) | ChatGPT | GPT-6.0 (theo thông tin nhóm cung cấp) | Consumer Lambda, DynamoDB, idempotency, `ORDER_CONFLICT`, SQS trigger, retry/DLQ, unit test, E2E, batch/replay, load test và tài liệu | **Đã tổng hợp theo thông tin nhóm cung cấp** |

> Thông tin model của Quân được cập nhật theo yêu cầu đại diện nhóm. **Trạng thái “Đã tổng hợp” là đã hoàn thiện khai báo của nhóm, không có nghĩa đã đối chiếu độc lập lịch sử hội thoại AI của Quân.** Mỗi sinh viên chịu trách nhiệm xác nhận độ chính xác nếu GVHD yêu cầu lịch sử prompt/model.

## 2. Phạm vi AI hỗ trợ — Nguyễn Đoàn Minh Khôi

- Giải thích vai trò API Gateway, Lambda, SQS, DynamoDB và SNS trong kiến trúc xử lý đơn hàng bất đồng bộ.
- Gợi ý Python `boto3`, `QUEUE_URL`, `send_message()`, dữ liệu JSON và Lambda Test Event cho Producer.
- Tham khảo validation với `customerId`, `productId`, `quantity`, malformed JSON và phản hồi `202/400/500`.
- Phân tích lỗi AWS Learner Lab và phương pháp đối soát invalid request không enqueue vào SQS.
- Hỗ trợ tổ chức source, ảnh AWS, README, bảng công việc và báo cáo Markdown.

## 3. Phạm vi AI hỗ trợ — Phạm Minh Quân

### 3.1. Công việc kỹ thuật

- **SQS Consumer Lambda:** tham khảo cách nhận nhiều record từ `event.Records`, parse `body`, kiểm tra message schema và xử lý lỗi một cách an toàn.
- **DynamoDB:** tham khảo `PutItem` với `ConditionExpression=attribute_not_exists(orderId)`, xử lý `ConditionalCheckFailedException` và đọc lại item bằng `ConsistentRead=True`.
- **Idempotency và conflict:** phân biệt retry cùng payload với cùng `orderId` nhưng payload khác; bảo vệ item đã `PROCESSED` trước ghi đè; giải thích `ORDER_CONFLICT`.
- **SQS trigger, retry và DLQ:** giải thích Event Source Mapping, visibility timeout, redrive policy `maxReceiveCount=5`, CloudWatch Logs và lỗi `INVALID_JSON`.
- **Batch/replay:** gợi ý cách thử batch hợp lệ, mixed batch và full-batch failure semantics bằng **direct Lambda invocation**, không đồng nhất với SQS batch thực tế.
- **Kiểm thử tích hợp:** tham khảo cách đối soát `orderId` xuyên suốt API Gateway → Producer → SQS → Consumer → DynamoDB và tổ chức small load test 10 request.
- **Unit tests/tài liệu:** tham khảo test cases, cấu trúc test, mô tả minh chứng AWS, README, bảng công việc và báo cáo tiến độ.

### 3.2. Nhóm prompt / nội dung yêu cầu AI hỗ trợ (đã tổng hợp)

Các dòng sau **diễn giải chủ đề trao đổi tương ứng với phần việc của Quân**, không được trình bày là bản chép nguyên văn lịch sử prompt:

1. Hướng dẫn cách đọc và xác thực các SQS records trong Consumer Lambda Python; xử lý trường hợp JSON hoặc schema không hợp lệ.
2. Giải thích cách sử dụng DynamoDB conditional `PutItem` theo `orderId` để tránh tạo đơn hàng trùng khi SQS gửi lại message.
3. Hướng dẫn phân biệt idempotent replay với `ORDER_CONFLICT` và cách đọc lại item bằng `ConsistentRead=True` mà không ghi đè dữ liệu gốc.
4. Giải thích cách kết nối SQS Event Source Mapping với Consumer Lambda, cấu hình batch size và concurrency trong AWS Learner Lab.
5. Phân tích cơ chế retry, redrive policy và Dead-Letter Queue khi Consumer lỗi `INVALID_JSON`; hướng dẫn xác minh qua CloudWatch Logs và DLQ.
6. Gợi ý Lambda Test Event cho batch 2 records hợp lệ, mixed batch và replay; giải thích full-batch failure semantics.
7. Hướng dẫn kiểm thử Full E2E và đối chiếu cùng `orderId` giữa API response và DynamoDB có trạng thái `PROCESSED`.
8. Gợi ý unit tests cho validation, idempotency và lỗi Consumer; tổ chức kịch bản small load 10 requests và trình bày kết quả thực nghiệm.
9. Hỗ trợ rà soát, phân loại 19 ảnh AWS, viết chú thích evidence và tài liệu GitHub phục vụ báo cáo Tuần 2.

### 3.3. Nội dung AI tạo ra hoặc gợi ý

- Ví dụ Python, giả mã và cách xử lý ngoại lệ cho Consumer/SQS/DynamoDB để tham khảo, rà soát rồi điều chỉnh theo mã nguồn thực tế.
- JSON mẫu, Lambda Test Event và các ca kiểm thử duplicate, conflict, invalid JSON, batch/replay.
- Phương pháp đối soát log, dữ liệu DynamoDB, queue/DLQ và kết quả API E2E.
- Gợi ý cấu trúc unit tests, tài liệu Markdown và cách gắn ảnh minh chứng vào báo cáo.

**Không khẳng định toàn bộ code Consumer, kết quả kiểm thử hoặc ảnh AWS do AI tạo ra.** Nguồn xác minh là source code, unit tests và minh chứng triển khai của nhóm.

## 4. Phần nhóm trực tiếp thực hiện và kiểm chứng

- Thao tác AWS Learner Lab ở Region `us-east-1` và sử dụng `LabRole`.
- Tạo/cấu hình SQS, DLQ, Lambda, API Gateway, DynamoDB và SNS theo từng giai đoạn.
- Deploy Producer/Consumer; chạy Test Event, API request và các phép thử trong phạm vi từng Lab.
- Kiểm tra CloudWatch Logs, message SQS/DLQ, item DynamoDB, idempotency, conflict, batch/replay và small load test.
- Chụp và phân loại ảnh AWS thực tế; review/chỉnh sửa source, tests và Markdown trước khi đưa lên GitHub.
- Tạo commit, Pull Request và đối soát các kết quả đã merge vào `main`.

## 5. Giới hạn minh chứng và đường dẫn đối chiếu

- Full E2E, retry/DLQ, conflict, direct batch/replay và small load Tuần 2 được xác minh trên **Lab Quân**; validation Producer và quan sát SQS được ghi nhận trên **Lab Khôi**.
- Batch nhiều records ở Tuần 2 là **direct Lambda invocation**, không phải minh chứng SQS trigger gom batch lớn hơn 1.
- Các kết quả **15/15 unit tests Consumer** và **10/10 HTTP 202** thuộc bộ kết quả đã ghi nhận; khai báo AI không thay thế dữ liệu kiểm thử.

**Mã nguồn và minh chứng:**

- [Producer Lambda](../src/producer/lambda_function.py), [Producer tests](../tests/test_producer.py), [10 ảnh AWS Khôi](../screenshots/week2/khoi/README.md).
- [Consumer Lambda](../src/consumer/lambda_function.py), [Consumer tests](../tests/test_consumer.py), [19 ảnh AWS Quân](evidence/week2/README.md).
- [PR #5 Consumer](https://github.com/pminhquan/cloud-async-orders/pull/5), [PR #7 Producer](https://github.com/pminhquan/cloud-async-orders/pull/7), [PR #8 tổng hợp](https://github.com/pminhquan/cloud-async-orders/pull/8), [PR #9 báo cáo](https://github.com/pminhquan/cloud-async-orders/pull/9).

**Kết luận khai báo:** Phần sử dụng AI của hai thành viên đã được nhóm tổng hợp theo thông tin cung cấp và phân công kỹ thuật. Nhóm trực tiếp chịu trách nhiệm về mã nguồn, triển khai, số liệu và minh chứng AWS trong báo cáo.

## 6. Phạm vi AI trong Tuần 3–4

Tuần 3 có AI hỗ trợ công cụ benchmark/load/metrics, monitoring IaC, unit tests, CI, rà soát và tài liệu. Kết quả đo được đối chiếu với JSON/CSV và ảnh thực tế, không suy từ gợi ý của công cụ.

Ngày 29/10/2026, Codex hỗ trợ đối chiếu source và thao tác qua phiên Console/CloudShell của Lab Quân do người dùng đăng nhập. Phạm vi gồm cập nhật deployment Producer từ source main sẵn có, bật mapping đúng nguồn, chạy E2E/validation/replay/conflict có giới hạn và quan sát một phép thử retry. Những thao tác này không được trình bày là sinh viên tự thực hiện thủ công. Antigravity Desktop hỗ trợ rà soát offline, kiểm thử và công cụ trình bày tài liệu; không có thay đổi source/test/script/IaC của ứng dụng trong Tuần 4.

AI hỗ trợ tổng hợp inventory, phân tích B1/B2/B3, tra nguồn giá AWS và soạn báo cáo/kịch bản. Các bản che định danh từng được tạo trong quá trình rà soát; ảnh lưu trong repository đã được khôi phục nguyên bản theo yêu cầu học phần, giữ thông tin sinh viên và MSSV. Không tạo lại giao diện Console hoặc tự dựng kết quả. Bản quan sát AWS, kiểm thử mô phỏng dịch vụ và minh chứng lịch sử được phân biệt trong [báo cáo Tuần 4](week4-report.md) và [nguồn minh chứng](evidence/week4/README.md).

Hai thành viên chịu trách nhiệm rà soát tài liệu, xác nhận khai báo công cụ đúng thực tế và giải thích mã nguồn, phương pháp cùng kết quả khi trình bày học phần.
