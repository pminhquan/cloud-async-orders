# Infrastructure as Code

## Tuần 1–2

Nhóm triển khai tài nguyên trực tiếp trên AWS Learner Lab bằng Console để tập trung hiểu dịch vụ và hoàn thiện luồng xử lý.

Trong Tuần 1–2, **không coi IaC là deliverable đã triển khai**.

## Tuần 3 (`iac/week3-monitoring.yaml`)

Bổ sung CloudFormation template nhẹ cho tầng **CloudWatch Monitoring & SNS Alerting**, tương thích giới hạn AWS Learner Lab:
- **Không tạo IAM User hoặc IAM Role mới** (tuân thủ nghiêm ngặt ràng buộc Lab).
- **Không hard-code AWS Account ID hoặc ARN cá nhân**; tham chiếu SNS Topic sẵn có (`order-dlq-alert`) qua parameter `AlertSnsTopicArn`.
- Định nghĩa `DLQVisibleMessagesAlarm` theo dõi metric `ApproximateNumberOfMessagesVisible` (`AWS/SQS`, `QueueName=orders-dlq`, ngưỡng `>= 1`, `TreatMissingData=notBreaching`).
- Hỗ trợ tuỳ chọn bật/tắt alarm cho `Errors` và `Throttles` của `order-consumer` (`EnableConsumerErrorAlarms`) và alarm backlog cho `orders-queue` (`EnableBacklogAlarm=false` mặc định để không áp đặt ngưỡng vận hành khi chưa đo thực tế).
- Gắn đầy đủ tags dự án (`Project=AsyncOrderProcessing`, `Owner=Khoi-Quan`).

Kiểm tra offline:

```bash
cfn-lint iac/week3-monitoring.yaml
python -m pytest -q tests/test_monitoring_and_metrics.py
```

Chi tiết kiến trúc giám sát và quy trình triển khai/kiểm chứng trên AWS Learner Lab xem tại:
- [docs/week3-monitoring.md](../docs/week3-monitoring.md)
- [docs/week3-aws-manual-runbook.md](../docs/week3-aws-manual-runbook.md)

## Giai đoạn sau

Nếu thời gian cho phép có thể dùng CloudFormation/SAM để mô tả:
- SQS main/DLQ;
- Lambda Producer/Consumer;
- DynamoDB;
- API Gateway;
- CloudWatch Alarm/SNS.

Không commit AWS credential vào template/repository.
