# Kế hoạch Tuần 2

Mục tiêu: tích hợp API → Producer → SQS → Consumer → DynamoDB trên AWS Learner Lab của Khôi tại `us-east-1`, kiểm tra xử lý lặp, retry/DLQ và thu thập minh chứng. Khôi thực hiện triển khai AWS; Quan phụ trách Consumer và các kịch bản kiểm thử liên quan. Cả hai chốt hợp đồng dữ liệu và đối soát E2E.

Theo xác nhận của nhóm, Tuần 1 đã được giảng viên duyệt. [Kế hoạch](week1-plan.md), [nhật ký](worklog/week1.md) và [minh chứng Tuần 1](evidence/week1/README.md) được giữ nguyên theo mốc lịch sử. Chưa có xác nhận nộp hoặc duyệt Tuần 2.

## 1. Mốc tiến độ và nguồn thông tin

- Nhóm đã thống nhất schema phẳng và môi trường tích hợp; xem [hợp đồng Tuần 2](integration-contract.md).
- Quan đã hoàn thành Consumer local trên `feat/week2-consumer-dynamodb`, commit [0192d2b](https://github.com/pminhquan/cloud-async-orders/commit/0192d2b554cf9795e21eb1b0b20dba8c4102c243), với kết quả local 15/15 unit tests đã qua. Theo bàn giao, [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5) đang mở, chưa merge; mã này chưa được triển khai AWS. Git local xác nhận commit chưa có trong `main` tại mốc `942a709`.
- Khôi tự báo cáo đã cấu hình các tài nguyên và kiểm thử riêng Producer → SQS, SQS → Consumer → DynamoDB thành công. Đây là kết quả tự báo cáo, chưa được xác minh độc lập bằng minh chứng AWS trong lượt cập nhật tài liệu này. Không coi Consumer đang triển khai là bản mã của Quan.
- **E2E chưa được xác minh:** `orderId=3435e200-ccd1-4664-90a8-633553d55188` do Producer tạo chưa có minh chứng đối chiếu trong log Consumer hoặc DynamoDB. Chưa đủ cơ sở kết luận đơn hàng đã được xử lý hoặc bị mất.
- Mốc cơ sở đã đối chiếu: `docs/week2-progress`, `main` và `origin/main` local cùng khớp đầu `main` trên remote tại `942a709`.

## 2. Nhiệm vụ Tuần 2

| Mã | Nhiệm vụ | Phụ trách | Tiến độ hiện có | Phần còn lại / điều kiện hoàn thành |
| :--- | :--- | :--- | :--- | :--- |
| W2-01 | Chốt schema, trạng thái và môi trường tích hợp | Cả hai | Đã thống nhất schema phẳng; dùng Lab của Khôi tại `us-east-1`. | Đối chiếu bản Producer/Consumer thực sự được triển khai với [hợp đồng](integration-contract.md). |
| W2-02 | Producer, API Gateway và SQS `SendMessage` | Khôi | Khôi báo cáo Producer → SQS thành công, `QUEUE_URL` đã cấu hình. Producer trên `main` local vẫn là PoC Tuần 1. | Bàn giao mã Producer đang chạy và minh chứng gửi SQS; xác nhận chỉ trả `202` khi gửi thành công, cùng phản hồi lỗi theo hợp đồng. |
| W2-03 | Consumer, DynamoDB conditional write và unit tests | Quan | Hoàn thành local: strict validation, `PROCESSED`, conditional `PutItem`, idempotency, log an toàn và 15 tests; commit `0192d2b`, PR #5 chưa merge. | Hoàn tất review/bàn giao theo quy trình nhóm; chưa coi là đã có trong `main` hoặc AWS. |
| W2-04 | Tích hợp và triển khai bản Consumer được chấp thuận | Cả hai | Chưa triển khai mã Quan. Khôi báo cáo đã có `order-consumer`, trigger và `TABLE_NAME=Orders`. | Quan bàn giao đúng phiên bản; nhóm chấp thuận tích hợp; Khôi triển khai và cung cấp phiên bản, cấu hình, quyền `PutItem`/`GetItem`, ESM để đối chiếu. |
| W2-05 | Đối soát E2E API → DynamoDB | Cả hai | Chưa xác minh E2E; còn thiếu dấu vết của UUID đã nêu ở mục 1. | Nối cùng `orderId` từ phản hồi API, SQS, log Consumer đến item DynamoDB có `PROCESSED`; lưu minh chứng. |
| W2-06 | Kiểm tra SQS redelivery idempotency và payload xung đột | Quan | Unit tests local đã có identical duplicate và conflicting duplicate. Chưa xác minh trên AWS. | Gửi lại cùng `orderId` và các trường ổn định; xác nhận không ghi đè. Đổi một trường nghiệp vụ phải báo lỗi và giữ item gốc. |
| W2-07 | Kiểm tra lỗi, retry và DLQ | Quan | Khôi báo cáo `maxReceiveCount=5`; chưa có minh chứng kiểm thử lỗi Tuần 2 được đối soát. | Theo dõi cùng tin nhắn lỗi qua retry → `orders-dlq`; kiểm tra lỗi dữ liệu/DB không bị coi là thành công. Không suy số invocation từ cấu hình receive count. |
| W2-08 | Kiểm tra batch nhiều tin nhắn và lỗi toàn lô | Quan | Local đã kiểm tra nhiều record, lỗi toàn batch và replay. Batch size 5/concurrency 5 trên AWS là thông tin Khôi báo cáo. | Kiểm tra batch hợp lệ và batch có lỗi trên AWS; record ghi trước lỗi phải deduplicate khi retry. Đối chiếu cờ partial-batch của ESM. |
| W2-09 | Kiểm thử tải nhỏ, có giới hạn | Cả hai | Chưa thực thi hoặc có log tải Tuần 2 được cung cấp. | Chốt trước số request, tốc độ, giới hạn concurrency theo [yêu cầu Lab](requirements.md) và điều kiện dừng; ghi số gửi/nhận/xử lý/lỗi thực đo. |
| W2-10 | Thu thập và đối soát minh chứng tích hợp | Cả hai | Có thông tin bàn giao và kết quả local; minh chứng AWS Tuần 2 còn chờ bổ sung. | Liên kết cấu hình, phiên bản mã, log và item/DLQ của từng ca; tách kết quả thực đo khỏi kết quả mong đợi, che thông tin nhạy cảm. |
| W2-11 | Nhật ký và tối thiểu 8 giờ thực tế/người | Cả hai | [Nhật ký Tuần 2](worklog/week2.md) ghi hoạt động đã biết; ngày và giờ thực tế còn TODO. | Mỗi người bổ sung ngày, thời lượng, kết quả, minh chứng; đối soát riêng từng người đạt ≥ 8 giờ thực tế, không tính giờ dự kiến hay thời gian AI chạy. |
| W2-12 | Báo cáo tiến độ tuần và khai báo AI | Khôi | Chưa có xác nhận chuẩn bị xong hoặc đã nộp báo cáo/khai báo AI Tuần 2. | Quan cung cấp và xác nhận phần SV1/AI của mình; Khôi tổng hợp, kiểm tra và nộp theo hướng dẫn giảng viên; lưu xác nhận thực tế. |

## 3. Phạm vi và các điểm còn chờ

Phần cốt lõi Tuần 2 gồm tích hợp, triển khai bản mã được chấp thuận, E2E, idempotency, retry/DLQ, batch, tải nhỏ, minh chứng và báo cáo. CloudWatch Alarm → SNS, benchmark FIFO, IaC và báo cáo chi phí cuối kỳ nằm ngoài phần cốt lõi, trừ khi giảng viên yêu cầu. Topic `order-dlq-alert` do Khôi báo cáo đã có không chứng minh luồng cảnh báo đã được tích hợp.

Các điểm chờ chính: PR #5 chưa merge; mã Consumer local chưa triển khai; mã Producer trên AWS chưa được đối chiếu với repo; quyền và cấu hình ESM chưa được kiểm tra trực tiếp; E2E/duplicate/conflict/retry/DLQ/batch/tải trên AWS còn thiếu minh chứng; ngày/giờ làm và việc nộp báo cáo chưa xác nhận. Việc tạo tài nguyên, nhận `202` hoặc qua unit tests không thay thế bằng chứng E2E.
