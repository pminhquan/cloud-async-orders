# Minh chứng triển khai AWS Tuần 3 - Nguyễn Đoàn Minh Khôi

**MSSV:** 24110259
**Dự án:** cloud-async-orders
**Ngày kiểm thử:** 24/10/2026
**AWS Region:** us-east-1

## 1. Nội dung thực hiện

- Kiểm tra SNS Topic order-dlq-alert và Email Subscription Confirmed.
- Kiểm thử gửi SNS trực tiếp và xác minh Gmail nhận được email.
- Phối hợp triển khai CloudWatch Alarm từ template của nhóm.
- Kiểm thử CloudWatch Alarm chuyển trạng thái thủ công và nhận email.
- Kiểm thử API Gateway POST /orders.
- Kiểm tra Lambda Consumer SQS Trigger và kích hoạt lại trigger bị Disabled.
- Xác minh dữ liệu đơn hàng được lưu trong DynamoDB Orders.

## 2. Kết quả kiểm thử

| Hạng mục | Kết quả |
| --- | --- |
| SNS Subscription | Confirmed |
| SNS Publish | Thành công, Gmail nhận email |
| CloudWatch | 3 Alarm được tạo và Actions Enabled |
| CloudWatch Alarm -> SNS -> Email | Thành công |
| API POST /orders hợp lệ | HTTP 202 Accepted |
| API POST /orders không hợp lệ | HTTP 400 Bad Request |
| Lambda Consumer Trigger | Enabled |
| DynamoDB Orders | PROCESSED |

## 3. Đối soát đơn hàng

- Order ID: 4894e467-298c-4963-a563-1eb5887982f7
- Customer ID: CUS-KHOI-W3
- Product ID: P001
- Quantity: 1
- Trạng thái sau xử lý: PROCESSED

## 4. Lưu ý về phạm vi kiểm thử

- HTTP 202 chỉ xác nhận API chấp nhận đơn hàng.
- DynamoDB PROCESSED xác nhận đơn hàng đã được xử lý và lưu.
- CloudWatch Alarm được kích hoạt thủ công để kiểm tra SNS Email.
- Đây không phải phép thử lỗi thực tế đi vào DLQ.
- Benchmark Standard/FIFO và đo hiệu năng do Quân phụ trách.

## 5. Ảnh minh chứng

- [W3-CW-DLQ-Alarm-History.png](evidence/week3/khoi/W3-CW-DLQ-Alarm-History.png)
- [W3-Khoi-API-Invalid-400.png](evidence/week3/khoi/W3-Khoi-API-Invalid-400.png)
- [W3-Khoi-API-POST-202.png](evidence/week3/khoi/W3-Khoi-API-POST-202.png)
- [W3-Khoi-DynamoDB-Order-Processed.png](evidence/week3/khoi/W3-Khoi-DynamoDB-Order-Processed.png)
- [W3-SNS-Alarm-Email-Received.png](evidence/week3/khoi/W3-SNS-Alarm-Email-Received.png)
- [W3-SNS-Email-Received.png](evidence/week3/khoi/W3-SNS-Email-Received.png)
- [W3-SNS-Topic-Publish-Success.png](evidence/week3/khoi/W3-SNS-Topic-Publish-Success.png)
- [W3-SNS-Topic-Subscription-Confirmed.png](evidence/week3/khoi/W3-SNS-Topic-Subscription-Confirmed.png)
