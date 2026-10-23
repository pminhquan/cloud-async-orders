# Infrastructure as Code (IaC)

## 1. Trạng thái theo tuần

- **Tuần 1–2:** Nhóm khởi tạo tài nguyên trực tiếp trên AWS Learner Lab Console để tập trung kiểm chứng từng dịch vụ và luồng tích hợp `API Gateway → Producer → SQS → Consumer → DynamoDB`.
- **Tuần 3 (`iac/week3-monitoring.yaml`):** Bổ sung CloudFormation template nhẹ cho tầng **CloudWatch Monitoring & SNS Alerting**, tương thích giới hạn AWS Learner Lab:
  - **Không tạo IAM User hoặc IAM Role mới** (tuân thủ nghiêm ngặt ràng buộc Lab).
  - **Không hard-code AWS Account ID hoặc ARN cá nhân**; tham chiếu SNS Topic sẵn có (`order-dlq-alert`) qua parameter `AlertSnsTopicArn`.
  - Định nghĩa `DLQVisibleMessagesAlarm` theo dõi metric `ApproximateNumberOfMessagesVisible` (`AWS/SQS`, `QueueName=orders-dlq`, ngưỡng `>= 1`, `TreatMissingData=notBreaching`).
  - Hỗ trợ tuỳ chọn bật/tắt alarm cho `Errors` và `Throttles` của `order-consumer` (`EnableConsumerErrorAlarms`) và alarm backlog cho `orders-queue` (`EnableBacklogAlarm=false` mặc định để không áp đặt ngưỡng vận hành khi chưa đo thực tế).
  - Gắn đầy đủ tags dự án (`Project=AsyncOrderProcessing`, `Owner=Khoi-Quan`).

## 2. Kiểm tra offline

```bash
python -m pytest -q tests/test_monitoring_and_metrics.py
```

Chi tiết kiến trúc giám sát và quy trình triển khai/kiểm chứng trên AWS Learner Lab xem tại:
- [docs/week3-monitoring.md](../docs/week3-monitoring.md)
- [docs/week3-aws-manual-runbook.md](../docs/week3-aws-manual-runbook.md)
