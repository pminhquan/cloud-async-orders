# Thiết Kế Kiến Trúc Hệ Thống (System Architecture Design)

Tài liệu mô tả kiến trúc kỹ thuật dự kiến, các thành phần cốt lõi, luồng xử lý thất bại và tiêu chuẩn sơ đồ kiến trúc cho hệ thống **cloud-async-orders**.

## 1. Các Thành Phần Dự Kiến (Planned Components)

Luồng hoạt động tổng thể:
`[Client] --(HTTPS POST /orders)--> [API Gateway] --> [order-producer] --> [orders-queue] --> [order-processor] --> [Orders (DynamoDB)]`

1. **Amazon API Gateway (`api-async-orders`)**: HTTP endpoint công khai tiếp nhận `POST /orders`, chuyển tiếp đến Producer Lambda.
2. **AWS Lambda (`order-producer`)**: Validate cú pháp body, gửi tin nhắn vào SQS, phản hồi `202 Accepted` cho client khi gửi thành công; trả về `400` nếu dữ liệu sai, `5xx` nếu gửi SQS thất bại.
3. **Amazon SQS (`orders-queue`)**: Hàng đợi đệm tách rời quá trình tiếp nhận và xử lý (Standard hoặc FIFO).
4. **AWS Lambda (`order-processor`)**: Nhận lô tin nhắn từ SQS Event Source Mapping, kiểm tra idempotency, ghi đơn hàng vào DynamoDB, và trả về danh sách `batchItemFailures`.
5. **Amazon DynamoDB (`Orders`)**: Bảng lưu trữ chi tiết đơn hàng với Partition Key `orderId`.
6. **Amazon SQS Dead Letter Queue (`orders-dlq`)**: Hàng đợi cô lập các tin nhắn không thể xử lý sau khi vượt ngưỡng `maxReceiveCount`. Cùng loại hàng đợi với queue nguồn (FIFO queue yêu cầu DLQ có hậu tố `.fifo`).
7. **Amazon CloudWatch Alarm (`dlq-alarm-messages-visible`)**: Giám sát chỉ số `ApproximateNumberOfMessagesVisible >= 1` trên hàng đợi DLQ.
8. **Amazon SNS Topic (`order-processing-alerts`)**: Nhận tín hiệu từ CloudWatch Alarm và gửi email cảnh báo tới quản trị viên.

## 2. Các Luồng Xử Lý Thất Bại (Failure Paths & Resilience)

1. **Lỗi validation tại Producer**: Client gửi thiếu trường hoặc sai kiểu dữ liệu -> `order-producer` trả về ngay mã `400 Bad Request`, không gửi tin nhắn vào SQS.
2. **Lỗi khi gửi tin nhắn vào SQS**: Sự cố mạng hoặc SQS tạm thời không khả dụng -> Producer ghi log tối thiểu mã lỗi/`orderId`, trả về `500 Internal Server Error` để client retry.
3. **Lỗi xử lý tạm thời tại Consumer**: DynamoDB bị throttling hoặc timeout mạng -> Consumer trả về ID tin nhắn lỗi trong `batchItemFailures`, SQS giữ tin nhắn và cho phép thử lại sau Visibility Timeout.
4. **Tin nhắn hỏng không thể xử lý (Poison Message)**: Lỗi logic kéo dài vượt quá `maxReceiveCount` lần nhận -> SQS tự động chuyển tin nhắn sang `orders-dlq`.
5. **Kích hoạt cảnh báo DLQ**: Tin nhắn xuất hiện trong DLQ -> CloudWatch Alarm chuyển sang trạng thái `ALARM`, kích hoạt thông báo email qua SNS Topic.

## 3. Checklist Sơ Đồ Kiến Trúc & Tình Trạng Bàn Giao

Tiêu chuẩn nghiệm thu sơ đồ kiến trúc chính thức:
- [ ] Thể hiện đầy đủ các thành phần theo checklist (API Gateway, Producer Lambda, SQS Queue, Consumer Lambda, DynamoDB, DLQ, CloudWatch Alarm, SNS Topic).
- [ ] Biểu diễn rõ luồng dữ liệu chính (Happy Path) và luồng xử lý lỗi (Failure Path sang DLQ và kích hoạt cảnh báo SNS).
- [ ] Phân định rõ ràng ranh giới trách nhiệm (Component & Trust Boundaries) và các giao thức tương tác (HTTPS, SDK SendMessage, Event Source Mapping, PutItem).

> [!IMPORTANT]
> **TÌNH TRẠNG SƠ ĐỒ (DIAGRAM STATUS)**: Tạo sơ đồ kiến trúc là **nhiệm vụ bàn giao chính thức của Tuần 1**, nhưng **HIỆN TẠI CHƯA CÓ FILE SƠ ĐỒ NÀO ĐƯỢC TẠO (NO DIAGRAM FILE CREATED YET)** trong phạm vi gói tài liệu nền tảng này. Không có file ảnh hoặc sơ đồ giả lập nào được đưa vào repo; sinh viên sẽ trực tiếp thiết kế và bàn giao file sơ đồ theo đúng kế hoạch Tuần 1.
