# Báo Cáo Nghiên Cứu Kỹ Thuật: Dịch Vụ Phụ Trách Của SV2 (Khôi)

Tài liệu tổng hợp nghiên cứu kỹ thuật các thành phần do SV2 (Khôi) phụ trách trong dự án **cloud-async-orders**: Amazon API Gateway, Producer Lambda (`order-producer`), Amazon DynamoDB (`Orders`), CloudWatch Alarms, Amazon SNS Topic và cơ chế retry/DLQ/alerting. Quan cung cấp thông tin DLQ và kết quả kiểm thử Consumer để phối hợp giám sát.

## 1. Ghi Chú Kỹ Thuật Có Trích Dẫn (Technical Notes)

| Dịch vụ / Khía cạnh | Ghi chú kỹ thuật & Phân tích giải pháp | Trích dẫn tài liệu AWS |
| :--- | :--- | :--- |
| **Amazon API Gateway** | **HTTP API vs REST API**: HTTP API có chi phí thấp hơn và hỗ trợ payload format 2.0 cho Lambda; REST API hỗ trợ request validation tại gateway và API keys. Đề xuất (**PROPOSED**): sử dụng HTTP API cho luồng tiếp nhận đơn hàng đơn giản hoặc REST API nếu cần validate schema tại gateway. | [API Gateway HTTP vs REST](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)<br>[Lambda API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html) |
| **Producer Lambda (`order-producer`)** | **Xử lý phản hồi & lỗi SQS**: Producer chỉ trả về `202 Accepted` sau khi gọi thành công `SendMessage` vào SQS; trả về `400 Bad Request` nếu payload sai; trả về `5xx` nếu gửi SQS thất bại để client retry với cùng `orderId`. AWS SDK có thể thử lại lệnh gửi trong giới hạn cấu hình; Producer không tự retry vô hạn. | [SQS SendMessage API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessage.html)<br>[AWS SDK Retry Behavior](https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html) |
| **Amazon DynamoDB (`Orders`)** | **Ghi nguyên tử có điều kiện**: Sử dụng `PutItem` với Condition Expression `attribute_not_exists(orderId)` để tránh ghi đè đơn hàng đã có. Khi trùng `orderId`, Consumer đọc và so sánh payload theo [hợp đồng tích hợp](../integration-contract.md) để phân biệt yêu cầu lặp với dữ liệu xung đột. | [DynamoDB Condition Expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)<br>[DynamoDB GetItem](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GetItem.html) |
| **CloudWatch Alarm & Amazon SNS** | **Giám sát DLQ & Cảnh báo Email**: Dự kiến đặt ngưỡng `ApproximateNumberOfMessagesVisible >= 1` trên DLQ; cần chốt period, số kỳ đánh giá và cách xử lý dữ liệu thiếu. SNS topic policy phải cho phép CloudWatch gửi thông báo; người nhận phải xác nhận đăng ký email (Confirmed Subscription). Chưa có minh chứng triển khai cảnh báo. | [CloudWatch Alarm Notifications](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Notify_Users_Alarm_Changes.html)<br>[SNS Email Notifications](https://docs.aws.amazon.com/sns/latest/dg/sns-email-notifications.html) |

## 2. Các Câu Hỏi Kỹ Thuật Tồn Đọng (Unresolved Questions)

- **Lựa chọn loại API Gateway**: Cần thống nhất chọn HTTP API hay REST API (**PROPOSED**, chờ nhóm chốt).
- **Quyền hạn LabRole thực tế**: Cần kiểm tra quyền `sqs:SendMessage` cho Producer và `dynamodb:PutItem` / `dynamodb:GetItem` cho Consumer theo thiết kế ghi có điều kiện và đọc đối chiếu khi trùng `orderId`. Quyền CloudWatch gửi đến SNS cần đối soát riêng qua topic policy; chưa xác minh đầy đủ các quyền cho giai đoạn tích hợp.
- **Tương thích Region & Hai tài khoản Lab**: PoC SV1 đã dùng `us-east-1`; cần xác nhận các thành phần SV2 tương thích Region này và chốt mô hình 1 tài khoản hay cross-account theo [docs/aws-inventory.md](../aws-inventory.md) (**CHƯA XÁC MINH / UNVERIFIED**).
- **Phân bổ giới hạn Concurrency**: Thống nhất phân bổ trần 10 concurrency giữa Producer Lambda và Consumer Lambda để không vượt quota tài khoản Lab.

## 3. Tiêu Chuẩn Bàn Giao & Nghiệm Thu (Acceptance Criteria)

- Báo cáo nghiên cứu bao quát đầy đủ các dịch vụ phụ trách, trích dẫn tài liệu AWS chính thức, phân định rõ nội dung đề xuất (PROPOSED) và hiện trạng thực tế (UNVERIFIED).
- Tích hợp nhất quán với hợp đồng dữ liệu tại [docs/integration-contract.md](../integration-contract.md) và danh mục tài nguyên tại [docs/aws-inventory.md](../aws-inventory.md).
