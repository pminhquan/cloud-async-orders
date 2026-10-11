# SQS Standard, FIFO và DLQ

## 1. So sánh kỹ thuật

| Khía cạnh | Standard | FIFO |
| :--- | :--- | :--- |
| Thứ tự | Best-effort; có thể nhận lệch thứ tự | Giữ thứ tự trong từng `MessageGroupId`, không bảo đảm thứ tự chung giữa các nhóm |
| Phân phối / chống gửi trùng | At-least-once; có thể nhận lại tin nhắn | Chặn gửi trùng trong 5 phút bằng `MessageDeduplicationId` hoặc hash body khi bật content-based deduplication |
| Thông lượng | Phù hợp tải lớn không yêu cầu thứ tự nghiêm ngặt | Phụ thuộc nhóm tin nhắn, cấu hình queue và Region |
| DLQ | Cùng loại với queue nguồn | Cùng loại, tên có hậu tố `.fifo`; chuyển tin lỗi sang DLQ có thể phá vỡ thứ tự nghiệp vụ |

Deduplication ở FIFO không thay thế idempotency: Consumer vẫn có thể nhận lại tin nhắn nếu đã ghi DB nhưng chưa xóa tin khỏi SQS. Hệ thống đích cần xử lý lặp an toàn theo [hợp đồng tích hợp](../integration-contract.md).

`maxReceiveCount` đếm số lần nhận, gồm lần đầu, không phải số lần retry thuần túy. SQS chuyển tin sang DLQ theo redrive policy khi chưa xử lý thành công; cấu hình 3 không cam kết đúng 3 invocation hoặc thời điểm cố định.

Nguồn AWS: [Standard](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html), [FIFO ordering](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html), [FIFO deduplication](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html), [DLQ](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html).

## 2. Kết quả Tuần 1 và phạm vi kiểm thử

PoC dùng Standard. Tin nhắn `ORD-W1-Q-003` có `POC_VALIDATED`; `ORD-W1-Q-ERR-002` có `INVALID_SCHEMA` lặp và được xác nhận trong `orders-dlq`. Nguồn: [minh chứng SQS → Consumer](../evidence/week1/README.md#w1-q-e2e). Consumer chỉ validate/log, chưa ghi DynamoDB hoặc có idempotency production.

Các ca dưới đây là kế hoạch cho giai đoạn sau, **chưa được thực thi trong PoC SV1 Tuần 1**. Kết quả SV2 riêng cần đối soát trước khi dùng làm bằng chứng tích hợp.

| Ca kiểm thử | Kết quả cần kiểm tra |
| :--- | :--- |
| API nhận payload sai | Trả `400`, không gửi SQS |
| Hai yêu cầu cùng `orderId` và payload | Conditional write giữ một bản ghi, xử lý lặp an toàn |
| FIFO gửi trùng trong/sau 5 phút | Cùng deduplication ID trong 5 phút chỉ tạo một tin; sau 5 phút có thể gửi lại nhưng DB vẫn giữ một bản ghi |
| Lô có tin hợp lệ và tin lỗi | Khi bật `ReportBatchItemFailures`, chỉ retry phần lỗi; FIFO dừng ở lỗi đầu tiên và trả cả tin lỗi/chưa xử lý |
| FIFO cùng `MessageGroupId` | Xử lý đúng thứ tự gửi |
| Cảnh báo DLQ | Alarm chuyển `ALARM` và xác nhận email SNS được giao |

Tải nhỏ có thể không tự phát sinh đảo thứ tự hoặc phân phối lặp trên Standard; cần chủ động gửi cùng `orderId` để kiểm tra idempotency.
