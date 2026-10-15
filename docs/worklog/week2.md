# Nhật ký hoạt động Tuần 2

Mỗi sinh viên phải ghi tối thiểu **8 giờ làm thực tế có tài liệu mỗi tuần** theo [yêu cầu dự án](../requirements.md). Khôi tổng hợp báo cáo tiến độ và khai báo AI; Quan cung cấp, xác nhận phần việc và việc sử dụng AI của mình.

Các bảng dưới ghi những hoạt động đã được cung cấp trong bàn giao Tuần 2. Chưa có ngày làm hoặc thời lượng thực tế, nên giữ `TODO`; không lấy ngày commit, timestamp log/ảnh, thời gian AI chạy hoặc thời lượng dự kiến thay cho giờ làm. Kết quả AWS đã xác minh thuộc Learner Lab của Quan tại `us-east-1`, có 19 ảnh PNG trong `docs/evidence/week2/`, đã push lên PR #6; kết quả của Khôi được ghi riêng là tự báo cáo. Kết quả local dùng mock được tách khỏi AWS thật. Lượt biên tập chỉ đối chiếu kết quả bàn giao và ảnh có sẵn, không chạy lại tests hoặc truy cập AWS.

## 1. SV1 — Quan

| Mã việc | Hoạt động | Ngày thực tế | Thời gian thực tế | Kết quả đã biết | Minh chứng / phần còn thiếu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| W2-03 | Nâng cấp Consumer theo schema phẳng; tích hợp DynamoDB, idempotency và log an toàn | TODO | TODO | Hoàn thành local trên `feat/week2-consumer-dynamodb`, commit `0192d2b`. PR #5 đang mở, chưa merge; Consumer từ PR #5 đã triển khai trên Lab của Quan. | [Mã Consumer tại commit](https://github.com/pminhquan/cloud-async-orders/blob/0192d2b554cf9795e21eb1b0b20dba8c4102c243/src/consumer/lambda_function.py), [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5). |
| W2-03, W2-06, W2-08 | Kiểm tra local: validation, duplicate/conflict, lỗi DB, nhiều record và replay | TODO | TODO | Kết quả local đã bàn giao: 15/15 unit tests qua; lời gọi DynamoDB được mock, không cần AWS hoặc credentials thật. Không coi đây là kiểm thử E2E hoặc xác nhận triển khai. | [Tests tại commit](https://github.com/pminhquan/cloud-async-orders/blob/0192d2b554cf9795e21eb1b0b20dba8c4102c243/tests/test_consumer.py). TODO: bổ sung liên kết log kiểm thử local vào bộ minh chứng nhóm. |
| W2-01, W2-04 | Tích hợp tài nguyên và triển khai Consumer trên Lab của Quan | TODO | TODO | `us-east-1`: `order-api` (HTTP API, `POST /orders`, stage `$default`), `order-producer`, `orders-queue`, `orders-dlq`, `order-consumer` từ PR #5, bảng `Orders`, khóa `orderId` (String), role `LabRole`. Trigger Enabled, batch size `1`, window `0`, concurrency `5`, Report batch item failures: `No`. | [Bảng Orders](../evidence/week2/W2-DynamoDB-Orders-Active.png), [trigger SQS](../evidence/week2/W2-Consumer-SQS-Trigger-Enabled.png). TODO: lưu đầy đủ thông tin phiên bản triển khai. |
| W2-03 | Consumer direct invocation trên AWS | TODO | TODO | PASS trên Lab của Quan; Lambda thành công, item DynamoDB được ghi với `status=PROCESSED`. | [Consumer direct test](../evidence/week2/W2-Consumer-Direct-Test-PASS.png), [item PROCESSED](../evidence/week2/W2-DynamoDB-Consumer-PROCESSED.png). |
| W2-06 | Replay cùng orderId và payload trên AWS | TODO | TODO | PASS trên Lab của Quan; Lambda thành công, item DynamoDB hiện có giữ nguyên theo kết quả đối soát nhóm cung cấp. Redelivery tự động qua SQS của duplicate chưa được xác minh riêng. | [Idempotency replay](../evidence/week2/W2-Consumer-Idempotency-Retry.png), [item DynamoDB](../evidence/week2/W2-DynamoDB-Consumer-PROCESSED.png). |
| W2-06 | Kiểm tra payload xung đột trên AWS | TODO | TODO | PASS trên Lab của Quan; dùng lại `orderId=TEST-QUAN-W2-001`, đổi `quantity` từ `2` sang `3`; Lambda báo `ORDER_CONFLICT`, DynamoDB giữ `quantity=2` và `status=PROCESSED`. | [ORDER_CONFLICT](../evidence/week2/W2-Consumer-Order-Conflict-PASS.png), [item không bị ghi đè](../evidence/week2/W2-Consumer-Conflict-NoOverwrite.png). |
| W2-02 | Producer direct invocation và API Gateway trên Lab của Quan | TODO | TODO | Producer direct test PASS, HTTP `202`, gửi message vào SQS; `POST /orders` qua API Gateway PASS, HTTP `202`. | [Producer direct test](../evidence/week2/W2-Producer-Direct-Test-PASS.png), [trạng thái queue](../evidence/week2/W2-Producer-SQS-Message-Received.png), [API POST /orders](../evidence/week2/W2-API-Gateway-POST-202.png). |
| W2-05 | Đối soát E2E API → Producer → SQS → Consumer → DynamoDB | TODO | TODO | PASS trên Lab của Quan; `orderId=e918c4af-3a9e-47c9-8a0c-13adbdfef82e` từ phản hồi API được tìm thấy trong DynamoDB với `status=PROCESSED`. | [API HTTP 202 và orderId](../evidence/week2/W2-API-Gateway-POST-202.png), [item E2E PROCESSED](../evidence/week2/W2-E2E-DynamoDB-PROCESSED.png). |
| W2-07 | Invalid JSON, retry và DLQ trên AWS | TODO | TODO | Lab của Quan: Consumer log `INVALID_JSON` và lỗi lặp lại; retry → DLQ PASS. Message ID `aa25ffee-aa5a-40ef-a224-347ed5c01523`, body `INVALID_MESSAGE_WEEK2` đã xác minh trong `orders-dlq`; redrive từ `orders-queue`, `maxReceiveCount=5`. Không suy số invocation từ receive count. | [Log INVALID_JSON](../evidence/week2/W2-Consumer-InvalidJSON-CloudWatch.png), [redrive](../evidence/week2/W2-SQS-Redrive-MaxReceiveCount-5.png), [số lượng queue/DLQ](../evidence/week2/W2-SQS-Retry-DLQ-Counts.png), [đúng message trong DLQ](../evidence/week2/W2-DLQ-Invalid-Message-Verified.png). |
| W2-08 | Batch hợp lệ qua gọi Lambda trực tiếp trên AWS | TODO | TODO | PASS trên Lab của Quan; event gồm 2 record định dạng SQS hợp lệ, Lambda trả `statusCode=200`, `processedCount=2`, cả hai record log `PROCESSED`. | [Batch hợp lệ](../evidence/week2/W2-Consumer-Batch-Valid-PASS.png). Đây là direct invocation; trigger SQS thực tế vẫn batch size `1`, chưa xác minh SQS tự gom batch nhiều record. |
| W2-08 | Batch hỗn hợp và replay qua gọi Lambda trực tiếp trên AWS | TODO | TODO | PASS theo kỳ vọng trên Lab của Quan: record đầu xử lý thành công, record thứ hai chứa invalid JSON; Lambda báo `INVALID_JSON` và invocation thất bại. Replay cùng event tiếp tục lỗi đúng kỳ vọng, item DynamoDB đã xử lý giữ nguyên theo kết quả đối soát nhóm cung cấp. | [Batch hỗn hợp](../evidence/week2/W2-Consumer-Batch-Mixed-Failure.png). Kết quả chỉ áp dụng cho direct invocation, chưa xác nhận SQS tự gom và phát lại batch nhiều record. |

Link tới commit xác định bản mã Consumer Tuần 2; việc đã triển khai trên Lab Quan và trạng thái PR #5 đang mở được ghi riêng, không suy ra mã đã merge vào `main`.

## 2. SV2 — Khôi

| Mã việc | Hoạt động | Ngày thực tế | Thời gian thực tế | Kết quả đã biết | Minh chứng / phần còn thiếu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| W2-02, W2-04 | Thiết lập tài nguyên và cấu hình Lab của Khôi | TODO | TODO | Khôi tự báo cáo đã có API, Producer, SQS/DLQ, Consumer, DynamoDB, SNS; đã đặt `QUEUE_URL`, `TABLE_NAME=Orders` và trigger. Chưa có minh chứng đối chiếu độc lập cho Lab này. | [Danh mục cấu hình được báo cáo](../integration-contract.md). TODO: liên kết minh chứng cấu hình và đúng phiên bản mã trên Lab Khôi; không dùng ảnh Lab Quan để xác nhận thay. |
| W2-02 | Kiểm thử riêng Producer → SQS trên Lab của Khôi | TODO | TODO | Khôi báo cáo thành công. Producer tạo `orderId=3435e200-ccd1-4664-90a8-633553d55188`; chưa xác nhận được cùng UUID ở log Consumer hoặc DynamoDB trên Lab này. | TODO: liên kết phản hồi API, kết quả `SendMessage` và dấu vết tin nhắn. Riêng E2E của Lab Khôi chưa được xác minh; E2E Lab Quan được ghi ở mục 1. |
| W2-04 | Kiểm thử riêng SQS → Consumer → DynamoDB trên Lab của Khôi | TODO | TODO | Khôi báo cáo thành công; chưa xác minh độc lập cho Lab này. Chưa đối chiếu được phiên bản Consumer đã dùng trên Lab Khôi. | TODO: liên kết log Consumer, item DynamoDB và phiên bản Consumer đã dùng. Không suy ra cả hai Lab đã độc lập qua mọi ca kiểm thử. |

## 3. Hoạt động chung và việc chưa hoàn thành

| Mã việc | Hoạt động | Ngày thực tế | Thời gian thực tế của mỗi người | Kết quả đã biết | Minh chứng / phần còn thiếu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| W2-01 | Thống nhất hợp đồng dữ liệu và môi trường tích hợp | TODO | Quan: TODO; Khôi: TODO | Nhóm dùng schema phẳng. Đã có kết quả tích hợp trên Lab Quan tại `us-east-1`; môi trường Khôi được ghi riêng theo báo cáo của Khôi. | [Hợp đồng](../integration-contract.md), [kế hoạch](../week2-plan.md). Không suy ra ngày họp, thời lượng hoặc biên bản họp từ thông tin này. |
| W2-02 | Đối soát kết quả Producer local dùng mock SQS | TODO | Quan: TODO; Khôi: TODO | Kết quả được bàn giao: PASS; đây là kiểm thử local dùng mock, tách khỏi Producer direct test và API Gateway trên AWS. Chưa có thông tin người thực hiện hoặc giờ làm để phân bổ. | [PR #7 — Producer SQS integration](https://github.com/pminhquan/cloud-async-orders/pull/7) đang mở. TODO: bổ sung log local và người thực hiện. |
| W2-09 | Kiểm thử tải nhỏ có giới hạn trên Lab của Quan | TODO | Quan: TODO; Khôi: TODO | PASS; 10 request `POST /orders` tuần tự, cách nhau khoảng 1 giây, cả 10 trả HTTP `202`. Lọc DynamoDB theo `customerId=CUS-LOAD-W2` trả 10 item, tất cả `PROCESSED`. | [10 request HTTP 202](../evidence/week2/W2-API-Small-Load-Test.png), [10 item PROCESSED](../evidence/week2/W2-Small-Load-DynamoDB-PROCESSED.png). Đối soát theo `customerId`, chưa xác nhận từng UUID; chỉ là tải nhỏ có giới hạn, chưa có kết quả stress test/benchmark. Chưa có giờ làm để phân bổ cho từng người. |
| W2-10 | Thu thập tài liệu và minh chứng Tuần 2 | TODO | Quan: TODO; Khôi: TODO | 19 ảnh PNG AWS thật của Lab Quan có sẵn trong `docs/evidence/week2/`, đã push lên PR #6; liên kết theo từng ca, gồm E2E/retry/DLQ trước đó và conflict, batch gọi trực tiếp, tải nhỏ mới bổ sung. | [PR #6 — tài liệu và 19 ảnh AWS](https://github.com/pminhquan/cloud-async-orders/pull/6) đang mở. TODO: bổ sung minh chứng cho các ca còn chờ; không coi PR đang mở là đã nộp giảng viên. |

Các việc sau vẫn là kế hoạch/chờ thực thi, chưa được ghi thành hoạt động hoàn thành hoặc giờ làm:

- W2-03–W2-04: hoàn tất review/bàn giao PR #5, lưu thông tin phiên bản triển khai; Consumer đã chạy trên Lab Quan, không còn là việc chờ triển khai ở Lab này.
- W2-05–W2-08: bổ sung minh chứng riêng cho Lab Khôi; redelivery tự động của duplicate, lỗi DB và SQS tự gom batch nhiều record trên AWS còn chờ xác minh riêng. Lab Quan đã có kết quả E2E, replay giống hệt, payload xung đột, retry/DLQ và batch hợp lệ/hỗn hợp, replay qua gọi Lambda trực tiếp.
- W2-09–W2-10: tải nhỏ 10 request tuần tự trên Lab Quan đã PASS theo đối soát `customerId`; chưa xác nhận từng UUID và chưa có kết quả stress test/benchmark. Bổ sung log local, thông tin phiên bản và minh chứng còn thiếu; bộ 19 ảnh đã có không xác nhận thay kết quả Lab Khôi.
- W2-11–W2-12: bổ sung nhật ký thực tế, tổng hợp báo cáo tuần và khai báo AI; việc nộp chưa xác nhận.

## 4. Đối soát giờ làm và báo cáo

| Sinh viên | Tổng giờ thực tế đã cung cấp | Đạt ≥ 8 giờ thực tế có tài liệu? | Thông tin còn phải bổ sung |
| :--- | :--- | :--- | :--- |
| Quan | TODO — chưa có tổng giờ để cộng | Chưa xác nhận | Ngày làm, thời lượng từng hoạt động, kết quả và minh chứng; tự xác nhận phần SV1/AI. |
| Khôi | TODO — chưa có tổng giờ để cộng | Chưa xác nhận | Ngày làm, thời lượng từng hoạt động, kết quả và minh chứng; tổng hợp riêng báo cáo tuần/AI. |

Chỉ cộng giờ khi có ghi nhận thực tế của từng người; cùng tham gia một hoạt động không có nghĩa hai người có cùng thời lượng. Việc đã đạt giờ hoặc được duyệt Tuần 1 không chứng minh đã đạt giờ Tuần 2. Chưa có xác nhận Tuần 2 đã được nộp hoặc được giảng viên duyệt.
