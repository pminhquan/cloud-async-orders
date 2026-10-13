# BÁO CÁO TIẾN ĐỘ TUẦN 1

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Nhóm:** Serverless  
**Môn học:** CLC0332779_05UTExMC - Điện toán đám mây  
**GVHD:** TS. Huỳnh Xuân Phụng  
**Region sử dụng:** `us-east-1`

## Sinh viên thực hiện

| MSSV | Họ và tên |
|---|---|
| 24110311 | Phạm Minh Quân |
| 24110259 | Nguyễn Đoàn Minh Khôi |

---

## 1. Phân chia công việc tuần 1

| STT | Công việc | Nội dung chính | Người thực hiện |
|---:|---|---|---|
| 1 | Tìm hiểu dịch vụ | Tìm hiểu nguyên lý hoạt động và vai trò của SQS Standard/FIFO, DLQ, Lambda, API Gateway, DynamoDB, CloudWatch và SNS trong hệ thống xử lý đơn hàng bất đồng bộ. | Khôi, Quân |
| 2 | Thiết kế kiến trúc | Xác định các thành phần chính của hệ thống và luồng dữ liệu: API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB; luồng lỗi qua DLQ → CloudWatch Alarm → SNS. | Khôi, Quân |
| 3 | Vẽ sơ đồ kiến trúc | Vẽ sơ đồ tổng thể hệ thống, thể hiện luồng xử lý đơn hàng và luồng xử lý message lỗi làm cơ sở cho các tuần tích hợp tiếp theo. | Quân, Khôi góp ý |
| 4 | Dựng nền SQS/DLQ/Consumer | Tạo SQS, DLQ, Consumer Lambda; kiểm thử message hợp lệ, message lỗi và cơ chế retry/DLQ ở mức PoC. | Quân |
| 5 | Dựng nền API/Producer | Tạo DynamoDB `Orders`, Lambda `order-producer`, API Gateway `order-api`, route `POST /orders`; kiểm thử Lambda/API trả HTTP 202. | Khôi |
| 6 | Tạo cảnh báo ban đầu | Tạo SNS topic `order-dlq-alert`, cấu hình Email Subscription và xác nhận trạng thái `Confirmed`. | Khôi |
| 7 | Chuẩn hóa tài nguyên | Sử dụng Region `us-east-1`, LabRole và gắn tag `Project/Owner` cho các tài nguyên đã triển khai. | Khôi, Quân |
| 8 | Tài liệu và GitHub | Chuẩn hóa source code, README, báo cáo, ảnh minh chứng và repository Public của nhóm. | Khôi, Quân |

---

## 2. Mức độ hoàn thành tuần 1

| STT | Công việc | Kết quả đạt được | Mức độ hoàn thành |
|---:|---|---|---:|
| 1 | Tìm hiểu dịch vụ | Đã nắm được vai trò của các dịch vụ Serverless chính, hiểu mô hình Producer–Queue–Consumer và cơ chế xử lý lỗi bằng DLQ. | 100% |
| 2 | Thiết kế kiến trúc | Đã xác định được kiến trúc tổng thể, luồng xử lý chính và luồng xử lý lỗi của hệ thống. | 100% |
| 3 | Vẽ sơ đồ kiến trúc | Đã hoàn thành sơ đồ tổng thể phục vụ báo cáo và làm cơ sở tích hợp trong Tuần 2. | 100% |
| 4 | SQS/DLQ/Consumer PoC | Đã tạo và kiểm thử độc lập SQS, DLQ, Consumer Lambda; message hợp lệ được xử lý, message lỗi có thể retry và chuyển DLQ. | 90% |
| 5 | API/Producer PoC | Đã tạo API Gateway và Producer Lambda; kiểm thử `POST /orders` thành công và nhận HTTP `202 Accepted`. | 100% |
| 6 | DynamoDB | Đã tạo bảng `Orders`, partition key `orderId`, sử dụng chế độ On-demand. | 100% |
| 7 | SNS | Đã tạo topic `order-dlq-alert` và xác nhận Email Subscription thành công. | 100% |
| 8 | Tích hợp toàn hệ thống | Các thành phần đã được kiểm thử riêng ở mức PoC; chưa tích hợp hoàn chỉnh Producer → SQS → Consumer → DynamoDB. | 50% |
| 9 | Tài liệu/GitHub | Đã chuẩn bị source code, báo cáo Tuần 1, tài liệu, worklog và ảnh minh chứng trên nhánh riêng phục vụ kiểm tra tiến độ. | 100% |

---

## 3. Công việc dự kiến tuần 2

Tuần 2 tập trung chuyển từ việc kiểm thử độc lập từng thành phần sang tích hợp hoàn chỉnh luồng xử lý đơn hàng bất đồng bộ.

| STT | Công việc | Nội dung dự kiến |
|---:|---|---|
| 1 | Thống nhất cấu trúc dữ liệu | Thống nhất định dạng JSON/message giữa Producer Lambda và Consumer Lambda để hai phía sử dụng cùng một cấu trúc dữ liệu. |
| 2 | Tích hợp Producer Lambda với SQS | Cập nhật `order-producer` để sau khi API Gateway nhận request hợp lệ, Lambda tạo message và gửi thật vào SQS thay vì chỉ trả kết quả PoC. |
| 3 | Cấu hình truy cập Queue | Cấu hình Queue URL hoặc biến môi trường cần thiết để Producer Lambda gửi message đúng vào SQS. |
| 4 | Kết nối SQS với Consumer Lambda | Hoàn thiện Event Source Mapping để SQS kích hoạt Consumer Lambda khi có message mới. |
| 5 | Cấu hình batch và concurrency | Thiết lập batch size phù hợp và kiểm tra maximum concurrency theo giới hạn của đề tài, bảo đảm concurrency không vượt mức yêu cầu. |
| 6 | Hoàn thiện Consumer Lambda | Cập nhật Consumer để đọc message đơn hàng, parse JSON, kiểm tra dữ liệu và xử lý theo cấu trúc đã thống nhất. |
| 7 | Ghi dữ liệu vào DynamoDB | Kết nối Consumer Lambda với bảng `Orders` và lưu dữ liệu đơn hàng sau khi xử lý. |
| 8 | Kiểm thử luồng tích hợp | Kiểm thử toàn bộ luồng `Client → API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB`. |
| 9 | Kiểm thử lỗi và retry | Kiểm tra trường hợp Consumer xử lý lỗi, cơ chế retry và quá trình message được chuyển sang DLQ. |
| 10 | Kiểm tra log | Theo dõi CloudWatch Logs của Producer và Consumer để xác nhận dữ liệu được xử lý đúng qua từng bước. |
| 11 | Cập nhật tài liệu và GitHub | Bổ sung source code, ảnh minh chứng, log thực thi, README và commit riêng theo từng phần công việc. |

---

## 4. GitHub Public

**Repository chính:**  
https://github.com/pminhquan/cloud-async-orders

**Nhánh minh chứng đầy đủ Tuần 1:**  
https://github.com/pminhquan/cloud-async-orders/tree/week1-full-evidence

Nhánh `week1-full-evidence` được sử dụng để tổng hợp source code, tài liệu, test, worklog và ảnh minh chứng của cả hai thành viên trong Tuần 1.

---

## 5. Chi tiết công việc đã thực hiện

### 5.1. Phần thực hiện của Nguyễn Đoàn Minh Khôi

Trong Tuần 1, Khôi tập trung thực hiện phần đầu vào của hệ thống và các tài nguyên liên quan đến việc tiếp nhận đơn hàng.

Các công việc đã thực hiện:

- Tạo bảng DynamoDB `Orders`.
- Thiết lập partition key là `orderId`.
- Cấu hình DynamoDB sử dụng chế độ On-demand.
- Tạo Lambda `order-producer`.
- Xây dựng xử lý nhận request tạo đơn hàng.
- Tạo API Gateway `order-api`.
- Cấu hình route `POST /orders`.
- Kết nối API Gateway với Producer Lambda.
- Kiểm thử Lambda Producer.
- Kiểm thử API và xác nhận nhận được HTTP `202 Accepted`.
- Chuẩn bị script PowerShell kiểm thử API.
- Tạo SNS topic `order-dlq-alert`.
- Tạo Email Subscription.
- Xác nhận Email Subscription ở trạng thái `Confirmed`.
- Thu thập ảnh minh chứng DynamoDB, Lambda Producer, API Gateway và SNS.
- Kiểm tra các tài nguyên hoạt động tại Region `us-east-1`.
- Sử dụng `LabRole` trong môi trường AWS Learner Lab.
- Phối hợp với Quân kiểm tra kiến trúc tổng thể của hệ thống.

### 5.2. Phần thực hiện của Phạm Minh Quân

Trong Tuần 1, Quân tập trung triển khai phía hàng đợi và Consumer.

Các công việc đã thực hiện:

- Tạo SQS Queue phục vụ tiếp nhận message đơn hàng.
- Tạo Dead Letter Queue.
- Liên kết Queue chính với DLQ.
- Cấu hình retry và redrive.
- Tạo Consumer Lambda.
- Kết nối SQS với Consumer Lambda.
- Kiểm thử Consumer với message hợp lệ.
- Kiểm thử Consumer với message không hợp lệ.
- Kiểm tra quá trình retry.
- Kiểm tra message được chuyển sang DLQ.
- Kiểm tra nội dung message trên Queue và DLQ.
- Thu thập CloudWatch Logs.
- Thu thập ảnh minh chứng SQS, DLQ, Lambda Consumer và IAM LabRole.
- Hoàn thiện sơ đồ kiến trúc tổng thể.
- Phối hợp với Khôi chuẩn bị cho bước tích hợp Tuần 2.

### 5.3. Phần thực hiện chung

Cả hai thành viên phối hợp:

- Tìm hiểu kiến trúc Serverless.
- Tìm hiểu mô hình Producer–Queue–Consumer.
- Xác định luồng xử lý chính:

`Client → API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB`

- Xác định luồng xử lý lỗi:

`Consumer Lambda → Retry → DLQ → CloudWatch Alarm → SNS`

- Thống nhất Region `us-east-1`.
- Sử dụng `LabRole`.
- Chuẩn hóa cấu trúc source code.
- Xây dựng integration contract.
- Chuẩn hóa README.
- Xây dựng worklog.
- Tổng hợp báo cáo Tuần 1.
- Tổ chức ảnh minh chứng theo từng thành viên.

---

## 6. Minh chứng trực tiếp trên GitHub

### 6.1. Phạm Minh Quân

**Consumer Lambda:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/src/consumer/lambda_function.py

**Unit test Consumer:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/tests/test_consumer.py

**Ảnh tạo SQS Queue:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-main-created.png

**Ảnh tạo DLQ:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-dlq-created.png

**Ảnh liên kết Queue với DLQ:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-dlq-linked.png

**Ảnh Consumer Lambda triển khai:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-lambda-consumer-deployed.png

**Ảnh Consumer Lambda test thành công:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-lambda-valid-test-success.png

**Ảnh log retry/error:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-lambda-retry-error-logs.png

**Ảnh message được chuyển vào DLQ:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-dlq-message-arrived.png

### 6.2. Nguyễn Đoàn Minh Khôi

**Producer Lambda:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/src/producer/lambda_function.py

**Script PowerShell kiểm thử API:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/scripts/test-order-api.ps1

**Ảnh DynamoDB Orders:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/01-dynamodb-orders.png

**Ảnh Lambda Producer HTTP 202:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/02-lambda-producer-202.png

**Ảnh API Gateway route POST /orders:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/03-api-route-post-orders.png

**Ảnh kiểm thử API bằng PowerShell – HTTP 202:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/04-api-powershell-202.png

**Ảnh SNS topic:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/05-sns-topic.png

**Ảnh SNS Email Subscription Confirmed:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/06-sns-email-confirmed.png

### 6.3. Tài liệu chung

**Phân công công việc:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/task-assignment.md

**Worklog Tuần 1:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/worklog/week1.md

**Integration contract Producer ↔ Consumer:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/integration-contract.md

---

## 7. Minh chứng công việc theo thành viên

### 7.1. Phạm Minh Quân

| Công việc | Link minh chứng |
|---|---|
| Consumer Lambda | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/src/consumer/lambda_function.py |
| Unit test Consumer | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/tests/test_consumer.py |
| Tạo SQS Queue | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-main-created.png |
| Tạo DLQ | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-dlq-created.png |
| Liên kết Queue với DLQ | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-dlq-linked.png |
| Consumer Lambda triển khai | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-lambda-consumer-deployed.png |
| Consumer test thành công | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-lambda-valid-test-success.png |
| Retry/error | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-lambda-retry-error-logs.png |
| Message vào DLQ | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv1/week1-sqs-dlq-message-arrived.png |
| Worklog | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/worklog/week1.md |

### 7.2. Nguyễn Đoàn Minh Khôi

| Công việc | Link minh chứng |
|---|---|
| Producer Lambda | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/src/producer/lambda_function.py |
| Script PowerShell test API | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/scripts/test-order-api.ps1 |
| DynamoDB Orders | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/01-dynamodb-orders.png |
| Lambda Producer HTTP 202 | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/02-lambda-producer-202.png |
| API Gateway POST /orders | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/03-api-route-post-orders.png |
| API PowerShell HTTP 202 | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/04-api-powershell-202.png |
| SNS topic | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/05-sns-topic.png |
| Email Subscription Confirmed | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/screenshots/week1/sv2/06-sns-email-confirmed.png |
| Worklog | https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/worklog/week1.md |

---

## 8. Minh chứng commit

Nhánh sử dụng để kiểm tra lịch sử commit:

https://github.com/pminhquan/cloud-async-orders/tree/week1-full-evidence

Các commit chính của Tuần 1 gồm:

| Nội dung commit | Người thực hiện |
|---|---|
| `feat: hoàn thiện SQS DLQ Consumer Lambda và kiểm thử tuần 1` | Phạm Minh Quân |
| `feat: hoàn thiện Producer API Gateway DynamoDB SNS và minh chứng tuần 1` | Nguyễn Đoàn Minh Khôi |
| `docs: tổng hợp đầy đủ báo cáo kiến trúc và minh chứng tuần 1` | Khôi, Quân |

Các commit trên tương ứng với source code, tài liệu và ảnh minh chứng đã được dẫn link trực tiếp trong các mục trên.

Sau khi cập nhật báo cáo và khai báo AI, nhóm tiếp tục tạo commit tài liệu để lưu lại nội dung đã chỉnh sửa theo góp ý của GVHD.

**Commit cập nhật khai báo AI và sửa link minh chứng:**  
`Sẽ bổ sung link commit trực tiếp sau khi commit thay đổi lên GitHub.`

---

## 9. Khai báo sử dụng AI

Trong quá trình thực hiện Tuần 1, nhóm có sử dụng công cụ AI để hỗ trợ tham khảo, giải thích kiến thức và hỗ trợ hoàn thiện quá trình triển khai.

**Công cụ AI:** ChatGPT  
**Model sử dụng:** GPT-5.6 Sol

### 9.1. Prompt/Nội dung yêu cầu AI hỗ trợ

Nhóm sử dụng AI để hỗ trợ các nội dung:

- Tìm hiểu vai trò của SQS Standard/FIFO, DLQ, Lambda, API Gateway, DynamoDB, CloudWatch và SNS.
- Tham khảo kiến trúc hệ thống xử lý đơn hàng bất đồng bộ.
- Phân tích luồng:

`API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB`

- Phân tích luồng xử lý lỗi:

`Consumer Lambda → Retry → DLQ → CloudWatch Alarm → SNS`

- Tham khảo mã Python mẫu cho Producer Lambda và Consumer Lambda.
- Tham khảo JSON kiểm thử.
- Hỗ trợ viết lệnh PowerShell gọi API.
- Hỗ trợ phân tích lỗi trong quá trình cấu hình và kiểm thử.
- Gợi ý cách tổ chức repository, README, worklog và báo cáo tiến độ.

### 9.2. Nội dung AI tạo ra

AI hỗ trợ:

- Giải thích kiến trúc Serverless và mô hình xử lý bất đồng bộ.
- Đề xuất luồng kết nối giữa các dịch vụ AWS.
- Cung cấp mã nguồn mẫu để tham khảo.
- Gợi ý cấu hình ban đầu cho Lambda và SQS.
- Gợi ý dữ liệu JSON dùng để test.
- Gợi ý lệnh PowerShell kiểm thử API.
- Hỗ trợ trình bày báo cáo và tài liệu GitHub.

### 9.3. Phần nhóm trực tiếp thực hiện và chỉnh sửa

Nhóm trực tiếp:

- Đăng nhập và triển khai tài nguyên trên AWS Learner Lab.
- Tạo và cấu hình SQS.
- Tạo DLQ và cấu hình redrive.
- Tạo Lambda Producer và Consumer.
- Tạo API Gateway.
- Tạo DynamoDB.
- Tạo SNS topic và Email Subscription.
- Sử dụng `LabRole`.
- Kiểm thử message hợp lệ và không hợp lệ.
- Kiểm thử retry/DLQ.
- Kiểm thử API Gateway.
- Kiểm tra CloudWatch Logs.
- Chụp ảnh minh chứng thực tế.
- Kiểm tra, chỉnh sửa và chạy thử mã nguồn trước khi đưa lên GitHub.

Các nội dung do AI gợi ý không được sử dụng nguyên trạng mà được nhóm kiểm tra và điều chỉnh theo kết quả triển khai thực tế trên AWS Learner Lab.

### 9.4. Minh chứng phần được nhóm chỉnh sửa và triển khai

**Producer Lambda:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/src/producer/lambda_function.py

**Consumer Lambda:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/src/consumer/lambda_function.py

**Unit test Consumer:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/tests/test_consumer.py

**Script kiểm thử API:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/scripts/test-order-api.ps1

**Phân công công việc:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/task-assignment.md

**Worklog Tuần 1:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/worklog/week1.md

**Integration contract:**  
https://github.com/pminhquan/cloud-async-orders/blob/week1-full-evidence/docs/integration-contract.md

---

## 10. Kết luận Tuần 1

Trong Tuần 1, nhóm đã hoàn thành việc tìm hiểu dịch vụ, thiết kế kiến trúc và triển khai các PoC riêng cho hai phía của hệ thống.

Phía Quân đã xây dựng và kiểm thử SQS, DLQ và Consumer Lambda.

Phía Khôi đã xây dựng DynamoDB, Producer Lambda, API Gateway và SNS, đồng thời kiểm thử API trả về HTTP `202 Accepted`.

Hiện tại hệ thống vẫn đang ở giai đoạn PoC riêng cho từng thành phần và chưa được tích hợp hoàn chỉnh theo luồng:

`API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB`

Việc tích hợp hoàn chỉnh sẽ được thực hiện trong Tuần 2.

Toàn bộ source code, test, tài liệu, worklog và ảnh minh chứng đã được lưu công khai trên GitHub.

**Repository chính:**  
https://github.com/pminhquan/cloud-async-orders

**Nhánh minh chứng Tuần 1:**  
https://github.com/pminhquan/cloud-async-orders/tree/week1-full-evidence