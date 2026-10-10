# Báo Cáo Nghiên Cứu: Amazon SQS Standard vs FIFO & Cơ Chế DLQ

Tài liệu so sánh kỹ thuật định tính giữa Amazon SQS Standard Queue và SQS FIFO Queue, phân tích cơ chế Dead Letter Queue (DLQ), làm rõ ranh giới giữa Deduplication và Idempotency, và lập kế hoạch các kịch bản kiểm thử cho hệ thống **cloud-async-orders**.

## 1. So Sánh Định Tính Amazon SQS Standard vs FIFO Queue

- **Thứ tự tin nhắn (Ordering)**:
  - *Standard*: Thứ tự xử lý dạng nỗ lực tối đa (best-effort ordering); trong điều kiện phân tán hoặc tải cao có thể bị lệch thứ tự.
  - *FIFO*: Bảo đảm tuyệt đối thứ tự gửi và nhận đúng trình tự First-In-First-Out trong phạm vi từng `MessageGroupId`.
- **Phân phối & Chặn trùng lặp (Delivery & Deduplication)**:
  - *Standard*: Phân phối ít nhất một lần (at-least-once delivery); có thể xảy ra trường hợp phân phối tin nhắn lặp lại.
  - *FIFO*: Hỗ trợ chặn gửi trùng lặp (suppresses duplicate SEND) trong cửa sổ 5 phút dựa trên `MessageDeduplicationId` hoặc content hash. **FIFO KHÔNG bảo đảm consumer không bao giờ nhận lại tin nhắn** (ví dụ: nếu consumer crash sau khi ghi DB nhưng trước khi xóa tin nhắn khỏi SQS) và **KHÔNG thay thế cơ chế idempotency ở cấp cơ sở dữ liệu (Database Idempotency)**.
- **Thông lượng (Throughput)**:
  - *Standard*: Mở rộng quy mô thông lượng sẵn sàng (scales readily), phù hợp lưu lượng truy cập lớn không phụ thuộc thứ tự.
  - *FIFO*: Thông lượng bị ràng buộc bởi cấu hình nhóm tin nhắn (`MessageGroupId`), thiết lập hàng đợi và Region (không đưa ra các con số cố định chưa kiểm chứng).
- **Cấu hình & Tác động DLQ**:
  - Hàng đợi DLQ phải có cùng loại với hàng đợi nguồn (queue FIFO bắt buộc sử dụng DLQ có hậu tố `.fifo`).
  - Đối với FIFO, việc chuyển một tin nhắn lỗi sang DLQ có thể làm gián đoạn chuỗi thứ tự xử lý nghiệp vụ nghiêm ngặt của `MessageGroupId` đó.
- **Nguyên lý DLQ & Redrive Policy**:
  - Tham số `maxReceiveCount` là số lần nhận tin nhắn (Receive count, bao gồm cả lần nhận đầu tiên), không phải số lần retry thuần túy. Khi tin nhắn vượt ngưỡng nhận theo redrive policy mà chưa được xử lý thành công, SQS tự động chuyển sang DLQ (không hứa hẹn số lần retry cố định).

*Tài liệu kỹ thuật AWS chính thức*:
- [SQS Standard Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)
- [SQS FIFO Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html)
- [SQS Dead-Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
- [SQS FIFO Exactly-Once Processing](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)

## 2. Kế Hoạch Kịch Bản Kiểm Thử Dự Kiến (Planned Test Scenarios)

Trong một bài test tải nhỏ với Standard Queue, hiện tượng đảo thứ tự hoặc phân phối lặp có thể không xuất hiện tự nhiên; do đó kịch bản kiểm thử cần chủ động gửi lặp `orderId` để kiểm tra idempotency:

- **Từ chối payload không hợp lệ tại API**: Gửi payload thiếu trường hoặc sai kiểu dữ liệu -> Kỳ vọng: API Gateway / Producer trả về `400 Bad Request`, không gửi SQS. *(Kết quả thực tế: Chưa thực thi / chưa có log)*.
- **Phân phối lặp đồng thời (Concurrent Duplicate Delivery)**: Gửi 2 yêu cầu mang cùng `orderId` và cùng payload -> Kỳ vọng: DynamoDB conditional write chặn ghi đè, xử lý lặp an toàn. *(Kết quả thực tế: Chưa thực thi / chưa có log)*.
- **Gửi trùng lặp trên FIFO & Kiểm tra DB (FIFO Duplicate-Send & DB Check)**: Gửi 2 tin nhắn cùng `MessageDeduplicationId` trong vòng 5 phút (kỳ vọng chỉ 1 tin nhắn đến consumer) và gửi lại sau 5 phút (kỳ vọng tin nhắn thứ 2 được gửi tới, nhưng conditional write DynamoDB giữ nguyên 1 bản ghi duy nhất) -> Kỳ vọng: DB chỉ có đúng 1 bản ghi đơn hàng. *(Kết quả thực tế: Chưa thực thi / chưa có log)*.
- **Xử lý lỗi theo lô từng phần (Partial Batch Failure)**: Gửi lô chứa tin nhắn lỗi và tin nhắn hợp lệ -> Kỳ vọng: Standard queue chỉ retry tin nhắn lỗi (`batchItemFailures`); FIFO queue handler dừng ở lỗi đầu tiên và trả về ID lỗi cùng các tin nhắn chưa xử lý phía sau để bảo toàn thứ tự. *(Kết quả thực tế: Chưa thực thi / chưa có log)*.
- **Bảo toàn thứ tự trên FIFO**: Gửi chuỗi tin nhắn có chung `MessageGroupId` -> Kỳ vọng: Nhận và xử lý nghiêm ngặt theo thứ tự đã gửi. *(Kết quả thực tế: Chưa thực thi / chưa có log)*.
- **Cách ly tin nhắn hỏng vào DLQ**: Inject trực tiếp payload hỏng vào test SQS (do Producer đã chặn payload hỏng ở tầng API) -> Kỳ vọng: Tin nhắn vượt ngưỡng nhận theo redrive policy được chuyển sang `orders-dlq`. *(Kết quả thực tế: Chưa thực thi / chưa có log)*.
- **Kích hoạt cảnh báo CloudWatch & SNS**: Kích hoạt chỉ số DLQ có tin nhắn -> Kỳ vọng: CloudWatch Alarm chuyển sang trạng thái `ALARM` và xác nhận email cảnh báo SNS chuyển giao thành công (confirmed SNS email delivery). *(Kết quả thực tế: Chưa thực thi / chưa có log)*.

> [!NOTE]
> **Hiện trạng thực tế**: Toàn bộ các kịch bản kiểm thử trên là kế hoạch nghiên cứu kỹ thuật lý thuyết; **chưa có bất kỳ kịch bản nào được thực thi trên môi trường AWS** trong Tuần 1.
