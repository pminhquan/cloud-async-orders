# BÁO CÁO TIẾN ĐỘ TUẦN 2

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda\
**Nhóm:** Serverless\
**Môn học:** CLC0332779_05UTExMC – Điện toán đám mây\
**Giảng viên hướng dẫn:** TS. Huỳnh Xuân Phụng\
**AWS Region:** `us-east-1`\
**Repository chính:** https://github.com/pminhquan/cloud-async-orders\
**Mốc đối chiếu GitHub:** nhánh `main`, merge PR #8 tại commit [`a55fbbe`](https://github.com/pminhquan/cloud-async-orders/commit/a55fbbe278019972785883d3793ff3b8c2faac1c) (17/10/2026).

## Sinh viên thực hiện

| MSSV | Họ và tên | Phụ trách chính |
|---|---|---|
| 24110311 | Phạm Minh Quân | Consumer Lambda, SQS/DLQ, DynamoDB, idempotency, tích hợp E2E và kiểm thử |
| 24110259 | Nguyễn Đoàn Minh Khôi | API Gateway, Producer Lambda, validation, kiểm thử SQS, minh chứng và tổng hợp tài liệu |

> **Phạm vi báo cáo:** Kết quả AWS E2E, retry/DLQ, conflict, batch và small load được ghi nhận trên Learner Lab của Quân. Kết quả kiểm thử trực tiếp Producer và các ảnh so sánh SQS được ghi nhận trên Learner Lab của Khôi. Không suy diễn rằng hai Lab đã thực hiện cùng toàn bộ các bài kiểm thử.

---

## 1. Phân chia công việc Tuần 2

| STT | Công việc | Nội dung thực hiện | Người phụ trách |
|---:|---|---|---|
| 1 | Chuẩn hóa Integration Contract | Thống nhất message JSON phẳng gồm `orderId`, `customerId`, `productId`, `quantity`, `status`, `createdAt`. | Khôi và Quân |
| 2 | Hoàn thiện Producer Lambda | Kiểm tra dữ liệu đầu vào, tạo order, gửi message hợp lệ vào `orders-queue` thông qua `sqs.send_message()`. | Khôi |
| 3 | Kiểm thử Producer và API | Kiểm tra Lambda với dữ liệu hợp lệ/không hợp lệ; đối chiếu API Gateway `POST /orders` trên Lab tích hợp. | Khôi; Quân hỗ trợ đối soát API E2E |
| 4 | Kiểm tra validation và SQS | Xác minh request sai trả `400`; kiểm tra hàng đợi trước và sau phép thử để quan sát việc không enqueue message sai. | Khôi |
| 5 | Hoàn thiện Consumer Lambda | Đọc SQS event, kiểm tra schema, ghi DynamoDB, ghi log an toàn và xử lý lỗi. | Quân |
| 6 | Idempotency và `ORDER_CONFLICT` | Dùng conditional write, kiểm tra duplicate hợp lệ và ngăn payload xung đột ghi đè dữ liệu đã lưu. | Quân |
| 7 | SQS Event Source Mapping | Kết nối `orders-queue` với `order-consumer`, kiểm tra trigger, batch size và giới hạn concurrency. | Quân; Khôi phối hợp |
| 8 | Retry và Dead-Letter Queue | Thử message không hợp lệ, theo dõi CloudWatch và xác nhận message được chuyển tới `orders-dlq`. | Quân |
| 9 | Full End-to-End | Đối soát `orderId` từ API Gateway đến DynamoDB trên Lab tích hợp của Quân. | Quân; Khôi phối hợp hoàn thiện Producer/schema |
| 10 | Batch, replay, tải nhỏ và báo cáo | Kiểm thử direct Lambda batch/replay, chạy 10 request tuần tự, thu thập ảnh và hoàn thiện GitHub/tài liệu. | Quân (kiểm thử), Khôi và Quân (tài liệu) |

**Tài liệu phân công trên GitHub:** [docs/task-assignment.md](task-assignment.md).\
**Kế hoạch công việc:** [docs/week2-plan.md](week2-plan.md).

---

## 2. Kết quả đạt được Tuần 2

| STT | Hạng mục | Kết quả và phạm vi xác minh |
|---:|---|---|
| 1 | Integration Contract | **Hoàn thành** – Producer và Consumer thống nhất cấu trúc message phẳng gồm 6 trường chính. |
| 2 | Producer gửi SQS | **PASS** – mã nguồn sử dụng `boto3` và `sqs.send_message()`; ảnh Lambda trực tiếp của Khôi ghi nhận `202`. |
| 3 | Input validation | **PASS** – direct Lambda test trên Lab Khôi: request hợp lệ trả `202`, request sai trả `400`. |
| 4 | Invalid request không enqueue | **PASS trong phép thử quan sát** – queue trước/sau giữ `8 available`, `0 in flight`; unit tests Producer cũng kiểm tra việc không gọi SQS với input sai. |
| 5 | Consumer ghi DynamoDB | **PASS trên Lab Quân** – item được lưu với `status = PROCESSED`. |
| 6 | Idempotency | **PASS trên Lab Quân** – replay cùng `orderId` và business payload không tạo bản ghi mới. |
| 7 | `ORDER_CONFLICT` | **PASS trên Lab Quân** – khác payload cùng `orderId` bị phát hiện, item cũ không bị overwrite. |
| 8 | Full E2E | **PASS trên Lab Quân** – cùng `orderId` xuất hiện trong API response và DynamoDB. |
| 9 | Retry/DLQ | **PASS trên Lab Quân** – Consumer ghi `INVALID_JSON`; message sau retry xuất hiện trong `orders-dlq`. |
| 10 | Batch hợp lệ | **PASS qua direct Lambda invocation** – 2 record hợp lệ, `processedCount = 2`. |
| 11 | Mixed batch/replay | **PASS theo thiết kế** – record invalid làm invocation fail theo full-batch semantics; replay được kiểm tra trực tiếp. |
| 12 | Small load | **PASS trên Lab Quân** – 10/10 HTTP `202`; 10 item được lọc theo `customerId = CUS-LOAD-W2` có `status = PROCESSED`. |
| 13 | Unit tests Consumer | **15/15 PASS** theo kết quả bàn giao tại [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5). |
| 14 | Kết quả test tổng hợp trước đó | Repository ghi nhận `33 passed, 81 subtests passed`; **chưa có lần chạy lại được xác nhận trên máy Khôi sau PR #8**. |
| 15 | GitHub Producer/Consumer | **Merged** – [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7) và [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5). |
| 16 | Báo cáo và minh chứng | **Merged** – [PR #8](https://github.com/pminhquan/cloud-async-orders/pull/8) vào `main`, có đủ 19 ảnh Quân và 10 ảnh Khôi. |

### 2.1. Giới hạn của các phép thử

Các ca Full E2E, retry/DLQ, conflict, batch/replay và small load được kiểm tra trên Lab Quân. Các ca validation ở Lab Khôi là **gọi Lambda trực tiếp**, không phải bằng chứng riêng rằng mọi request invalid đã được thử qua API Gateway ở Lab Khôi. Cấu hình SQS event source mapping trên Lab Quân sử dụng **batch size = 1**, **concurrency = 5**, giới hạn concurrency này không vượt quá mức tối đa 10 của đề tài. Vì vậy, bài batch gồm nhiều record là **direct invocation**, không chứng minh SQS tự gom nhiều record vào một lần gọi Lambda. Small load 10 request là bài kiểm thử tải nhỏ, không phải stress test hoặc benchmark hiệu năng lớn.

**Ma trận đối chiếu yêu cầu – nhiệm vụ – bằng chứng:** [docs/TRACEABILITY-W1-W2.md](TRACEABILITY-W1-W2.md).

---

## 3. Kiến trúc hệ thống và hợp đồng dữ liệu

### 3.1. Luồng xử lý chính

```text
Client
   ↓
API Gateway (POST /orders)
   ↓
order-producer (Lambda)
   ↓
orders-queue (Amazon SQS)
   ↓
order-consumer (Lambda)
   ↓
DynamoDB Orders (status = PROCESSED)
```

Sau khi tiếp nhận request hợp lệ, Producer tạo dữ liệu đơn hàng và gửi message đến SQS. Consumer được trigger từ SQS, đọc và xác thực message, sau đó ghi đơn hàng vào DynamoDB. HTTP `202 Accepted` thể hiện đơn hàng đã được tiếp nhận để xử lý bất đồng bộ, không có nghĩa là DynamoDB đã xử lý hoàn tất ngay tại thời điểm API phản hồi.

### 3.2. Luồng Retry/DLQ

```text
orders-queue
   ↓
order-consumer xử lý lỗi và invocation thất bại
   ↓
SQS retry theo visibility timeout/redrive policy
   ↓
orders-dlq (sau khi đạt điều kiện chuyển vào DLQ)
```

Trong bài kiểm thử ở Lab Quân, redrive policy sử dụng `maxReceiveCount = 5`. Consumer giữ **full-batch failure semantics**, chưa bật `ReportBatchItemFailures` cho giai đoạn này.

### 3.3. Schema message thống nhất

```json
{
  "orderId": "UUID",
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2,
  "status": "PENDING",
  "createdAt": "2026-10-15T00:00:00+00:00"
}
```

Producer tạo `orderId` dưới dạng UUID, thời gian `createdAt` theo UTC và gửi `status = PENDING`. Consumer kiểm tra các trường bắt buộc, chuyển trạng thái ghi vào DynamoDB thành `PROCESSED` và sử dụng conditional write:

```text
attribute_not_exists(orderId)
```

Nếu `orderId` đã tồn tại, Consumer đọc bản ghi với `ConsistentRead=True` rồi đối chiếu các trường `customerId`, `productId`, `quantity`, `createdAt`. Duplicate cùng business payload được chấp nhận theo cơ chế idempotency; payload khác bị coi là `ORDER_CONFLICT` và không được ghi đè.

**Tài liệu hợp đồng dữ liệu:** [docs/integration-contract.md](integration-contract.md).

---

## 4. Chi tiết công việc Nguyễn Đoàn Minh Khôi

### 4.1. Hoàn thiện Producer Lambda

Khôi đảm nhận cập nhật Producer từ PoC Tuần 1 sang phiên bản gửi đơn vào SQS trong Tuần 2. Mã nguồn hiện nằm tại [src/producer/lambda_function.py](../src/producer/lambda_function.py), gồm các xử lý chính:

- Nhận JSON request, kiểm tra `customerId`, `productId` là chuỗi không rỗng.
- Kiểm tra `quantity` là số nguyên dương; từ chối số không, số âm, chuỗi hoặc sai kiểu.
- Trả `400` nếu JSON không hợp lệ hoặc thiếu trường bắt buộc.
- Tạo UUID `orderId`, timestamp UTC `createdAt` và `status = PENDING`.
- Gửi message vào SQS bằng `boto3.client("sqs").send_message(...)` với `QUEUE_URL` đã cấu hình.
- Trả `202` sau khi SQS chấp nhận message; trả `500` nếu thao tác gửi SQS thất bại.
- Ghi log `ORDER_SENT_TO_SQS` khi gửi thành công.

### 4.2. Kết quả kiểm thử Producer

| Ca kiểm thử | Kết quả ghi nhận | Minh chứng |
|---|---|---|
| Payload hợp lệ | `202`, có `ORDER_SENT_TO_SQS` | [Ảnh 01](../screenshots/week2/khoi/01-producer-valid-202.png) |
| Thiếu `customerId` | `400` | [Ảnh 02](../screenshots/week2/khoi/02-producer-missing-customerid-400.png) |
| Thiếu `productId` | `400` | [Ảnh 03](../screenshots/week2/khoi/03-producer-missing-productid-400.png) |
| `quantity` không hợp lệ | `400` | [Ảnh 04](../screenshots/week2/khoi/04-producer-invalid-quantity-400-a.png), [05](../screenshots/week2/khoi/05-producer-invalid-quantity-400-b.png), [06](../screenshots/week2/khoi/06-producer-invalid-quantity-400-c.png) |
| JSON sai cú pháp | `400` | [Ảnh 07](../screenshots/week2/khoi/07-producer-invalid-json-400.png) |
| SQS trước invalid test | 8 available, 0 in flight | [Ảnh 08](../screenshots/week2/khoi/08-sqs-before-invalid-request.png) |
| Invalid request được từ chối | `400` | [Ảnh 09](../screenshots/week2/khoi/09-producer-invalid-request-400.png) |
| SQS sau invalid test | 8 available, 0 in flight | [Ảnh 10](../screenshots/week2/khoi/10-sqs-after-invalid-request.png) |

Số message hiển thị trên SQS không tăng qua phép thử invalid. Đây là quan sát snapshot, được củng cố bởi logic kiểm tra input trước `send_message()` trong source và các unit tests Producer.

### 4.3. Mã nguồn và minh chứng trên GitHub

- [Producer Lambda](../src/producer/lambda_function.py).
- [Unit tests Producer](../tests/test_producer.py).
- [PR #7 — Producer tích hợp SQS/validation (Merged)](https://github.com/pminhquan/cloud-async-orders/pull/7).
- [Thư mục 10 ảnh minh chứng Khôi](../screenshots/week2/khoi/).

---

## 5. Chi tiết công việc Phạm Minh Quân

### 5.1. Consumer Lambda và DynamoDB

Quân nâng cấp Consumer theo schema phẳng, đọc các record SQS, kiểm tra dữ liệu rồi ghi DynamoDB bằng `PutItem` có điều kiện. Chương trình dùng log có cấu trúc, giới hạn dữ liệu ghi log và bảo vệ bản ghi đã xử lý khi xảy ra duplicate. Mã nguồn nằm tại [src/consumer/lambda_function.py](../src/consumer/lambda_function.py). Bộ unit tests Consumer đã ghi nhận **15/15 PASS** trong quá trình PR #5.

### 5.2. Full End-to-End

Bài test trên AWS Learner Lab của Quân đã đi qua API Gateway, Producer, SQS, Consumer và DynamoDB. Kết quả được đối soát bằng cùng `orderId`:

```text
orderId = e918c4af-3a9e-47c9-8a0c-13adbdfef82e
status  = PROCESSED
```

Minh chứng: [API Gateway HTTP 202](evidence/week2/W2-API-Gateway-POST-202.png) và [item DynamoDB PROCESSED](evidence/week2/W2-E2E-DynamoDB-PROCESSED.png).

### 5.3. Idempotency và `ORDER_CONFLICT`

Replay cùng `orderId` và cùng business payload được Consumer xử lý an toàn mà không tạo bản ghi mới. Với `orderId = TEST-QUAN-W2-001`, khi thay đổi `quantity` từ `2` sang `3`, Consumer ghi nhận `ORDER_CONFLICT`, trong khi DynamoDB vẫn giữ bản ghi có `quantity = 2` và `status = PROCESSED`.

Minh chứng: [Idempotency replay](evidence/week2/W2-Consumer-Idempotency-Retry.png), [ORDER_CONFLICT](evidence/week2/W2-Consumer-Order-Conflict-PASS.png), [DynamoDB không overwrite](evidence/week2/W2-Consumer-Conflict-NoOverwrite.png).

### 5.4. Invalid JSON, retry và DLQ

Message chứa `INVALID_MESSAGE_WEEK2` làm Consumer ghi log `INVALID_JSON` và invocation thất bại. Sau khi được thử lại theo cấu hình SQS, message được xác nhận xuất hiện trong `orders-dlq`.

```text
Message ID: aa25ffee-aa5a-40ef-a224-347ed5c01523
Body: INVALID_MESSAGE_WEEK2
maxReceiveCount = 5
```

Minh chứng: [CloudWatch INVALID_JSON](evidence/week2/W2-Consumer-InvalidJSON-CloudWatch.png), [redrive policy](evidence/week2/W2-SQS-Redrive-MaxReceiveCount-5.png), [message trong DLQ](evidence/week2/W2-DLQ-Invalid-Message-Verified.png).

### 5.5. Direct batch và replay

Ở bài direct Lambda invocation, event chứa **2 record hợp lệ** trả `statusCode = 200` và `processedCount = 2`. Với mixed batch, record đầu hợp lệ, record tiếp theo chứa invalid JSON; Consumer ghi `INVALID_JSON` và invocation thất bại theo **full-batch failure semantics**. Replay cùng event tiếp tục thất bại tại record không hợp lệ; item đã xử lý không bị ghi đè nhờ cơ chế idempotency.

Minh chứng: [batch hợp lệ](evidence/week2/W2-Consumer-Batch-Valid-PASS.png), [mixed batch](evidence/week2/W2-Consumer-Batch-Mixed-Failure.png).

### 5.6. Small load test

Nhóm sử dụng 10 request `POST /orders` tuần tự, cách nhau khoảng một giây. Cả **10/10 request** trả HTTP `202`. Sau đó DynamoDB được lọc theo `customerId = CUS-LOAD-W2`, ghi nhận **10 item** với trạng thái `PROCESSED`. Đây là thử tải nhỏ, chưa đo throughput, độ trễ P95 hoặc giới hạn chịu tải.

Minh chứng: [10 API requests](evidence/week2/W2-API-Small-Load-Test.png), [10 items PROCESSED](evidence/week2/W2-Small-Load-DynamoDB-PROCESSED.png).

### 5.7. Mã nguồn và minh chứng trên GitHub

- [Consumer Lambda](../src/consumer/lambda_function.py).
- [Unit tests Consumer](../tests/test_consumer.py).
- [PR #5 — Consumer/DynamoDB/idempotency (Merged)](https://github.com/pminhquan/cloud-async-orders/pull/5).
- [Thư mục 19 ảnh minh chứng của Quân](evidence/week2/).

---

## 6. GitHub, Pull Request và lịch sử tích hợp

### 6.1. Repository dùng để nộp

**Repository:** https://github.com/pminhquan/cloud-async-orders\
**Nhánh chính:** `main`\
**Bản tài liệu/ảnh đã hợp nhất:** [Merge commit `a55fbbe`](https://github.com/pminhquan/cloud-async-orders/commit/a55fbbe278019972785883d3793ff3b8c2faac1c).

### 6.2. Các Pull Request chính

| Pull Request | Nội dung | Trạng thái | Commit trên `main` |
|---|---|---|---|
| [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5) | Consumer, DynamoDB, idempotency | **Merged** | `914de9b` |
| [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7) | Producer gửi SQS, input validation | **Merged** | `015d420` (squash) |
| [PR #8](https://github.com/pminhquan/cloud-async-orders/pull/8) | Báo cáo Tuần 1–2, ma trận đối chiếu và 29 ảnh AWS Tuần 2 | **Merged** | `a55fbbe` |
| [PR #6](https://github.com/pminhquan/cloud-async-orders/pull/6) | Nhánh tài liệu và ảnh Tuần 2 gốc của Quân | **Open tại mốc đối chiếu 17/10/2026** | Chưa merge riêng; **19 ảnh đã được đồng bộ vào `main` qua PR #8** |

### 6.3. Các commit tài liệu Tuần 1–2

| Commit | Nội dung |
|---|---|
| [`045daf0`](https://github.com/pminhquan/cloud-async-orders/commit/045daf0) | Kế hoạch, báo cáo, worklog và minh chứng Tuần 1 |
| [`648b165`](https://github.com/pminhquan/cloud-async-orders/commit/648b165) | Bổ sung 10 ảnh kiểm thử Producer/SQS của Khôi |
| [`09d0fd1`](https://github.com/pminhquan/cloud-async-orders/commit/09d0fd1) | Chỉ mục kiểm thử E2E, idempotency, retry/DLQ, batch và load |
| [`2a828f5`](https://github.com/pminhquan/cloud-async-orders/commit/2a828f5) | Kế hoạch, báo cáo và worklog Tuần 2 |
| [`7ad73cd`](https://github.com/pminhquan/cloud-async-orders/commit/7ad73cd) | Chuẩn hóa README, kiến trúc, phân công và tài liệu nộp |
| [`5a89fbe`](https://github.com/pminhquan/cloud-async-orders/commit/5a89fbe) | Đồng bộ 19 ảnh AWS của Quân, hoàn thiện liên kết và bảng đối chiếu |
| [`a55fbbe`](https://github.com/pminhquan/cloud-async-orders/commit/a55fbbe) | Merge PR #8 vào `main` |

Các file kỹ thuật và báo cáo quan trọng:

- [Producer](../src/producer/lambda_function.py) và [Consumer](../src/consumer/lambda_function.py).
- [Integration Contract](integration-contract.md).
- [Báo cáo Tuần 2](week2-report.md).
- [Báo cáo tổng hợp Tuần 1–2](bao-cao-tuan1-tuan2.md).
- [Ma trận đối chiếu yêu cầu](TRACEABILITY-W1-W2.md).

---

## 7. Minh chứng kiểm thử Tuần 2

### 7.1. Minh chứng của Phạm Minh Quân (19 ảnh)

**Thư mục đã có trên `main`:** [docs/evidence/week2/](evidence/week2/).

| Nhóm minh chứng | Hình ảnh trên GitHub |
|---|---|
| DynamoDB table và item | [Bảng Orders](evidence/week2/W2-DynamoDB-Orders-Active.png), [item PROCESSED](evidence/week2/W2-DynamoDB-Consumer-PROCESSED.png) |
| Producer và API | [Producer direct test](evidence/week2/W2-Producer-Direct-Test-PASS.png), [SQS nhận message](evidence/week2/W2-Producer-SQS-Message-Received.png), [API Gateway 202](evidence/week2/W2-API-Gateway-POST-202.png) |
| Trigger Consumer | [SQS event source mapping](evidence/week2/W2-Consumer-SQS-Trigger-Enabled.png), [Consumer direct test](evidence/week2/W2-Consumer-Direct-Test-PASS.png) |
| Full E2E | [DynamoDB đối soát orderId](evidence/week2/W2-E2E-DynamoDB-PROCESSED.png) |
| Idempotency/conflict | [Replay](evidence/week2/W2-Consumer-Idempotency-Retry.png), [ORDER_CONFLICT](evidence/week2/W2-Consumer-Order-Conflict-PASS.png), [item không overwrite](evidence/week2/W2-Consumer-Conflict-NoOverwrite.png) |
| Retry/DLQ | [CloudWatch INVALID_JSON](evidence/week2/W2-Consumer-InvalidJSON-CloudWatch.png), [redrive 5 lần](evidence/week2/W2-SQS-Redrive-MaxReceiveCount-5.png), [SQS/DLQ counts](evidence/week2/W2-SQS-Retry-DLQ-Counts.png), [message trong DLQ](evidence/week2/W2-DLQ-Invalid-Message-Verified.png) |
| Batch | [Batch valid](evidence/week2/W2-Consumer-Batch-Valid-PASS.png), [mixed batch](evidence/week2/W2-Consumer-Batch-Mixed-Failure.png) |
| Small load | [10 request](evidence/week2/W2-API-Small-Load-Test.png), [10 item PROCESSED](evidence/week2/W2-Small-Load-DynamoDB-PROCESSED.png) |

### 7.2. Minh chứng của Nguyễn Đoàn Minh Khôi (10 ảnh)

**Thư mục đã có trên `main`:** [screenshots/week2/khoi/](../screenshots/week2/khoi/).

10 ảnh bao gồm: Lambda hợp lệ trả `202`; thiếu `customerId`/`productId` trả `400`; các trường hợp `quantity` sai quy cách; malformed JSON; ảnh số lượng message SQS trước, trong và sau khi thử invalid request. Các đường dẫn từng ảnh đã được liệt kê ở **Mục 4.2**.

### 7.3. Tổng hợp minh chứng

Nhánh `main` hiện có **29 ảnh AWS Tuần 2**, trong đó Quân đóng góp 19 ảnh và Khôi đóng góp 10 ảnh. Các ảnh được liên kết trong [chỉ mục minh chứng Tuần 2](evidence/week2/README.md) và [ma trận đối chiếu](TRACEABILITY-W1-W2.md). Không cần merge lại PR #6 chỉ để lấy bộ ảnh này.

---

## 8. Nhật ký công việc Tuần 2

Các bảng dưới đây tổng hợp hoạt động có source, PR và bằng chứng AWS để đối chiếu với [worklog Tuần 2](worklog/week2.md). Nhật ký thời lượng được quản lý riêng theo yêu cầu học phần.

### 8.1. Phạm Minh Quân

| STT | Hoạt động | Kết quả/minh chứng |
|---:|---|---|
| 1 | Nâng cấp Consumer, tích hợp DynamoDB và conditional write | [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5), Consumer source |
| 2 | Xây dựng và rà soát unit tests Consumer | [tests/test_consumer.py](../tests/test_consumer.py) |
| 3 | Triển khai Consumer, cấu hình trigger SQS và thông số batch/concurrency | [Ảnh trigger](evidence/week2/W2-Consumer-SQS-Trigger-Enabled.png) |
| 4 | Kiểm thử Full E2E và đối soát API/DynamoDB bằng `orderId` | [API](evidence/week2/W2-API-Gateway-POST-202.png), [DynamoDB](evidence/week2/W2-E2E-DynamoDB-PROCESSED.png) |
| 5 | Kiểm thử idempotency, replay và `ORDER_CONFLICT` | [Replay](evidence/week2/W2-Consumer-Idempotency-Retry.png), [conflict](evidence/week2/W2-Consumer-Order-Conflict-PASS.png) |
| 6 | Kiểm tra Invalid JSON, retry, redrive và DLQ | [CloudWatch](evidence/week2/W2-Consumer-InvalidJSON-CloudWatch.png), [DLQ](evidence/week2/W2-DLQ-Invalid-Message-Verified.png) |
| 7 | Thử direct batch valid/mixed và replay | [Valid](evidence/week2/W2-Consumer-Batch-Valid-PASS.png), [mixed](evidence/week2/W2-Consumer-Batch-Mixed-Failure.png) |
| 8 | Thực hiện small load, chụp 19 ảnh và tổ chức evidence | [Ảnh load](evidence/week2/W2-API-Small-Load-Test.png), [bộ ảnh](evidence/week2/) |

### 8.2. Nguyễn Đoàn Minh Khôi

| STT | Hoạt động | Kết quả/minh chứng |
|---:|---|---|
| 1 | Thống nhất contract, hoàn thiện Producer và cấu hình gửi SQS | [PR #7](https://github.com/pminhquan/cloud-async-orders/pull/7), [source](../src/producer/lambda_function.py) |
| 2 | Xây dựng/rà soát validation, xử lý lỗi và các trường hợp input sai | [Producer tests](../tests/test_producer.py) |
| 3 | Kiểm thử trực tiếp Lambda với valid, missing field và malformed JSON | [10 ảnh Khôi](../screenshots/week2/khoi/) |
| 4 | Kiểm tra invalid request không làm tăng số message SQS | [SQS trước](../screenshots/week2/khoi/08-sqs-before-invalid-request.png), [sau](../screenshots/week2/khoi/10-sqs-after-invalid-request.png) |
| 5 | Phối hợp kiểm tra SQS backlog, queue và luồng Producer/Consumer | [Integration Contract](integration-contract.md) |
| 6 | Chụp, phân loại, đặt tên và đưa 10 ảnh minh chứng lên GitHub | [Commit `648b165`](https://github.com/pminhquan/cloud-async-orders/commit/648b165) |
| 7 | Tổng hợp báo cáo, đồng bộ tài liệu/ảnh nhóm và hoàn thiện PR #8 | [PR #8](https://github.com/pminhquan/cloud-async-orders/pull/8), [commit `5a89fbe`](https://github.com/pminhquan/cloud-async-orders/commit/5a89fbe) |

### 8.3. Tổng hợp và đối soát

Kết quả kỹ thuật được đối chiếu qua source, PR và minh chứng AWS. Nhật ký thời lượng tuân theo [yêu cầu học phần](requirements.md).

---

## 9. Khai báo sử dụng AI

Trong Tuần 2, AI được sử dụng để hỗ trợ tham khảo kiến thức về AWS Serverless, giải thích thiết kế Producer/Consumer, gợi ý validation, mô tả idempotency, hỗ trợ phân tích log, đề xuất test event và tổ chức tài liệu. **Việc cấu hình AWS, chạy các phép kiểm thử, chụp ảnh, đối soát DynamoDB/SQS và thao tác GitHub được nhóm thực hiện và kiểm tra dựa trên minh chứng thực tế.**

### 9.1. Công cụ và phạm vi sử dụng

Theo [bản khai báo AI trong repository](ai-declaration.md), Khôi ghi nhận sử dụng **ChatGPT / GPT-5.6 Sol**. Theo thông tin nhóm mới cung cấp, phần Quân được tổng hợp với **ChatGPT / GPT-6.0**. Mục khai báo của Quân đã cập nhật theo phạm vi công việc Consumer/DynamoDB/Retry/DLQ; đây là xác nhận **đã tổng hợp thông tin**, không phải đối soát độc lập lịch sử prompt nguyên văn.

Các nội dung AI tham khảo gồm:

- Giải thích SQS Event Source Mapping, redrive policy và Dead-Letter Queue.
- Hỗ trợ phân tích message schema giữa Producer và Consumer.
- Gợi ý xây dựng validation `202/400` và xử lý JSON không hợp lệ.
- Gợi ý Python/Lambda Test Event, unit test và các tình huống lỗi.
- Hỗ trợ lý giải DynamoDB conditional write, idempotency và `ORDER_CONFLICT`.
- Hỗ trợ đọc và phân tích CloudWatch Logs, retry/DLQ, batch và replay.
- Sắp xếp README, báo cáo, liên kết GitHub và bộ ảnh minh chứng.

### 9.2. Công việc nhóm trực tiếp triển khai

- Tạo và cấu hình tài nguyên trong AWS Learner Lab `us-east-1`, sử dụng `LabRole`.
- Triển khai Producer Lambda, Consumer Lambda, API Gateway, SQS/DLQ, DynamoDB và SNS theo giai đoạn.
- Thực hiện các bài test trực tiếp trên AWS và kiểm tra kết quả trả về.
- Đối chiếu cùng `orderId` giữa API response và DynamoDB; kiểm tra retry/DLQ.
- Chụp ảnh AWS, quản lý source/tests, review commit và merge các Pull Request.

### 9.3. Thông tin theo thành viên

| Thành viên | Thông tin AI đã có | Phạm vi ghi nhận | Ghi chú |
|---|---|---|---|
| Nguyễn Đoàn Minh Khôi | ChatGPT; model ghi trong hồ sơ: GPT-5.6 Sol | Producer/SQS, validation, troubleshooting, minh chứng, báo cáo | Đã tổng hợp theo khai báo trong GitHub |
| Phạm Minh Quân | ChatGPT / GPT-6.0 (theo thông tin nhóm cung cấp) | Consumer Lambda, DynamoDB conditional write, idempotency, `ORDER_CONFLICT`, SQS trigger, retry/DLQ, E2E, batch/replay, unit tests, tải nhỏ và tài liệu | **Đã tổng hợp theo thông tin nhóm cung cấp** |

### 9.4. Prompt và kết quả AI hỗ trợ phần Quân

Các chủ đề yêu cầu AI đã tổng hợp tương ứng với phần việc của Quân (diễn giải nội dung, **không phải bản chép prompt nguyên văn**):

- Gợi ý Consumer Python đọc SQS `Records`, validate JSON/schema và xử lý lỗi `INVALID_JSON`.
- Tham khảo conditional `PutItem`, `ConsistentRead=True`, idempotency và `ORDER_CONFLICT` để không ghi đè item cũ.
- Giải thích Event Source Mapping, redrive `maxReceiveCount=5`, retry/DLQ và CloudWatch Logs.
- Gợi ý Test Event và kịch bản direct batch valid/mixed/replay, full-batch failure semantics.
- Hỗ trợ thiết kế unit tests, E2E đối soát `orderId`, small load 10 request và cách trình bày 19 ảnh AWS.

AI cung cấp giải thích kỹ thuật, ví dụ code/JSON và phương án test để **tham khảo**. Quân/nhóm trực tiếp kiểm tra mã nguồn, cấu hình và kết quả trên AWS Learner Lab. Xem [khai báo AI chi tiết](ai-declaration.md) và [minh chứng của Quân](evidence/week2/README.md).

---

## 10. Kết luận Tuần 2

Sau Tuần 2, dự án đã chuyển từ các PoC tương đối độc lập của Tuần 1 sang pipeline xử lý đơn hàng bất đồng bộ được tích hợp và kiểm thử trên môi trường AWS Learner Lab của nhóm. Producer có khả năng validate request, tạo đơn hàng và gửi message hợp lệ vào SQS; Consumer đọc message, xác thực dữ liệu và ghi DynamoDB, đồng thời hỗ trợ idempotency và ngăn dữ liệu xung đột ghi đè.

Những mục tiêu cốt lõi đã có minh chứng gồm: request hợp lệ trả `202`, request sai trả `400`, Consumer lưu item `PROCESSED`, Full E2E đối soát cùng `orderId`, retry/DLQ với invalid JSON, direct batch/replay và small load 10/10 request. **Full E2E, retry/DLQ và load test đã được xác minh trên Lab Quân**; phần Khôi có bộ ảnh validation/SQS riêng.

Về GitHub, **PR #5** (Consumer), **PR #7** (Producer) và **PR #8** (báo cáo, liên kết, 29 ảnh minh chứng) đều đã được merge vào `main`. PR #6 vẫn là nhánh tài liệu gốc đang mở tại mốc đối chiếu, nhưng 19 ảnh của Quân đã được đưa vào `main` thông qua PR #8 nên không cần merge riêng chỉ vì các ảnh này.

Các nội dung còn thuộc các giai đoạn tiếp theo gồm cảnh báo CloudWatch Alarm kết nối SNS, benchmark thực tế so sánh SQS Standard/FIFO, thử tải lớn và đánh giá thông lượng/độ trễ. Bài báo cáo Tuần 2 chỉ kết luận các chức năng đã có mã nguồn và minh chứng kiểm thử phù hợp, không nhận các mục tiêu tương lai là đã hoàn thành.

**Repository chính thức:** https://github.com/pminhquan/cloud-async-orders\
**File trong repository:** `docs/week2-report.md`\
**Bằng chứng 29 ảnh:** https://github.com/pminhquan/cloud-async-orders/blob/main/docs/evidence/week2/README.md\
**Pull Request tổng hợp:** https://github.com/pminhquan/cloud-async-orders/pull/8.
