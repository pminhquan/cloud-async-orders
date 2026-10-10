# Báo Cáo Nghiên Cứu Kỹ Thuật: Dịch Vụ Phụ Trách Của SV2 (Khôi)

Tài liệu tổng hợp nghiên cứu kỹ thuật các thành phần do SV2 (Khôi) phụ trách trong dự án **cloud-async-orders**: Amazon API Gateway, Producer Lambda (`order-producer`), Amazon DynamoDB (`Orders`), Amazon SNS Topic và cơ chế retry/alerting (việc triển khai CloudWatch Alarm giữ nguyên vai trò phối hợp nhóm / Joint Coordination).

## 1. Ghi Chú Kỹ Thuật Có Trích Dẫn (Technical Notes)

| Dịch vụ / Khía cạnh | Ghi chú kỹ thuật & Phân tích giải pháp | Trích dẫn tài liệu AWS |
| :--- | :--- | :--- |
| **Amazon API Gateway** | **HTTP API vs REST API**: HTTP API tối ưu độ trễ, chi phí thấp hơn, hỗ trợ payload format 2.0; REST API hỗ trợ request validation tại gateway và API keys. Đề xuất (**PROPOSED**): sử dụng HTTP API cho luồng tiếp nhận đơn hàng đơn giản hoặc REST API nếu cần validate schema tại gateway. | [API Gateway HTTP vs REST](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)<br>[Lambda API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html) |
| **Producer Lambda (`order-producer`)** | **Xử lý phản hồi & lỗi SQS**: Producer chỉ trả về `202 Accepted` sau khi gọi thành công `SendMessage` vào SQS; trả về `400 Bad Request` nếu payload sai; trả về `5xx` nếu gửi SQS thất bại để client retry. Trách nhiệm retry ở tầng tiếp nhận thuộc về client, Producer không tự ý retry vô hạn. | [SQS SendMessage API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessage.html)<br>[Lambda SQS Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html) |
| **Amazon DynamoDB (`Orders`)** | **Ghi nguyên tử có điều kiện**: Sử dụng `PutItem` với Condition Expression `attribute_not_exists(orderId)` để bảo vệ dữ liệu chống ghi đè khi có trùng lặp. Khớp nối chặt chẽ với giao diện consumer của SV1 tại [docs/integration-contract.md](../integration-contract.md). | [DynamoDB Condition Expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html) |
| **CloudWatch Alarm & Amazon SNS** | **Giám sát DLQ & Cảnh báo Email**: CloudWatch Alarm theo dõi chỉ số `ApproximateNumberOfMessagesVisible >= 1` trên DLQ, gửi cảnh báo qua SNS Topic. Lưu ý người quản trị bắt buộc phải xác nhận đăng ký email (Confirmed Subscription) mới nhận được thông báo thực tế. | [CloudWatch Alarm Sends Email](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)<br>[SNS Email Notifications](https://docs.aws.amazon.com/sns/latest/dg/sns-email-notifications.html) |

## 2. Các Câu Hỏi Kỹ Thuật Tồn Đọng (Unresolved Questions)

- **Lựa chọn loại API Gateway**: Cần thống nhất chọn HTTP API hay REST API (**PROPOSED**, chờ nhóm chốt).
- **Quyền hạn LabRole thực tế**: Cần kiểm tra Console thực tế xem `LabRole` có đủ quyền thao tác với DynamoDB (`dynamodb:PutItem`), SQS (`sqs:SendMessage`), và SNS (`sns:Publish`) hay không (**CHƯA XÁC MINH / UNVERIFIED**).
- **Tương thích Region & Hai tài khoản Lab**: Xác định Region chung và mô hình triển khai 1 tài khoản hay cross-account theo phân tích tại [docs/aws-inventory.md](../aws-inventory.md) (**CHƯA XÁC MINH / UNVERIFIED**).
- **Phân bổ giới hạn Concurrency**: Thống nhất phân bổ trần 10 concurrency giữa Producer Lambda và Consumer Lambda để không vượt quota tài khoản Lab.

## 3. Tiêu Chuẩn Bàn Giao & Nghiệm Thu (Acceptance Criteria)

- Báo cáo nghiên cứu bao quát đầy đủ các dịch vụ phụ trách, trích dẫn tài liệu AWS chính thức, phân định rõ nội dung đề xuất (PROPOSED) và hiện trạng thực tế (UNVERIFIED).
- Tích hợp nhất quán với hợp đồng dữ liệu tại [docs/integration-contract.md](../integration-contract.md) và danh mục tài nguyên tại [docs/aws-inventory.md](../aws-inventory.md).
