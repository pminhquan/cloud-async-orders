# Nghiên cứu kỹ thuật — phần Khôi phụ trách

Tài liệu này tách **kiến thức/nguyên tắc thiết kế** khỏi **trạng thái triển khai thực tế**.

## 1. API Gateway + Producer

Thiết kế dùng `POST /orders`.

Producer cần:
- parse JSON;
- validate `customerId`, `productId`, `quantity`;
- tạo `orderId`;
- tạo `createdAt`;
- tạo `status=PENDING`;
- gọi `SQS SendMessage`;
- trả `202` chỉ khi gửi thành công;
- trả `400` khi input sai;
- trả `500` khi gửi SQS lỗi.

Trạng thái Tuần 2: **đã triển khai**.

## 2. DynamoDB

Table `Orders`, key `orderId`.

Consumer dùng:

```text
ConditionExpression = attribute_not_exists(orderId)
```

Nếu conditional write fail vì item đã tồn tại, đọc consistent item và so sánh business fields để phân biệt replay hợp lệ với conflict.

Trạng thái Tuần 2: **đã triển khai trên Consumer**.

## 3. SNS / CloudWatch Alarm

SNS topic `order-dlq-alert` đã tạo từ Tuần 1.

CloudWatch Alarm tự động cảnh báo DLQ là phần giai đoạn sau; không mô tả là đã nghiệm thu trong Tuần 2 nếu chưa có evidence.

## 4. Standard/FIFO

Tuần 2 chủ yếu dùng Standard queue. Benchmark/so sánh Standard/FIFO hoàn chỉnh được chuyển sang giai đoạn sau.

## 5. Tài liệu AWS tham khảo

- API Gateway HTTP vs REST: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- Lambda + API Gateway: https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html
- SQS SendMessage: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessage.html
- DynamoDB condition expressions: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html
- DynamoDB GetItem: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GetItem.html
- CloudWatch alarm notifications: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Notify_Users_Alarm_Changes.html
- SNS email: https://docs.aws.amazon.com/sns/latest/dg/sns-email-notifications.html
