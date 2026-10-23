# Giám sát CloudWatch & Cảnh báo SNS (W3-01)

## 1. Kiến trúc luồng giám sát và cảnh báo

```text
orders-queue (SQS Standard)
   ↓
order-consumer (AWS Lambda)
   ↓ (xử lý thất bại & retry vượt maxReceiveCount)
orders-dlq (SQS Dead Letter Queue)
   ↓ (Metric: ApproximateNumberOfMessagesVisible >= 1)
CloudWatch Alarm (DLQVisibleMessagesAlarm)
   ↓ (AlarmActions)
Amazon SNS Topic (order-dlq-alert)
   ↓
Email Notification (Confirmed Subscription)
```

---

## 2. Thiết kế Infrastructure as Code (`iac/week3-monitoring.yaml`)

File [`iac/week3-monitoring.yaml`](../iac/week3-monitoring.yaml) định nghĩa cấu hình giám sát tương thích với các ràng buộc của AWS Learner Lab:

1. **Không tạo IAM User/Role mới:** Chỉ khai báo tài nguyên `AWS::CloudWatch::Alarm`.
2. **Không tạo trùng SNS Topic và không hard-code Account ID:** Sử dụng parameter `AlertSnsTopicArn` để liên kết tới SNS Topic `order-dlq-alert` đã có từ Tuần 1.
3. **Cấu hình `DLQVisibleMessagesAlarm`:**
   - `Namespace`: `AWS/SQS`
   - `MetricName`: `ApproximateNumberOfMessagesVisible`
   - `Dimensions`: `QueueName = !Ref DLQName` (mặc định `orders-dlq`)
   - `Statistic`: `Maximum`
   - `Period`: `60` giây (hoặc `300` giây qua parameter `AlarmPeriodSeconds`)
   - `EvaluationPeriods`: `1` (cấu hình được qua `DLQEvaluationPeriods`)
   - `Threshold`: `1` (`ComparisonOperator: GreaterThanOrEqualToThreshold`)
   - `TreatMissingData`: `notBreaching`
4. **Ý nghĩa của `TreatMissingData = notBreaching`:**
   - Khi hàng đợi `orders-dlq` hoàn toàn rỗng và không có hoạt động trong một số chu kỳ, hoặc khi CloudWatch có độ trễ điểm dữ liệu, trạng thái thiếu datapoint sẽ được coi là **không vi phạm ngưỡng** (`OK`), tránh báo động giả (false alarm).
   - Ngay khi có ít nhất `1` message hiển thị trong `orders-dlq` (`Maximum >= 1`), alarm chuyển sang trạng thái `ALARM` và kích hoạt `AlarmActions` gửi thông báo tới `AlertSnsTopicArn`.
5. **Các Alarm bổ trợ có điều kiện:**
   - `ConsumerErrorsAlarm` (`AWS/Lambda`, `Errors >= 1`) và `ConsumerThrottlesAlarm` (`AWS/Lambda`, `Throttles >= 1`) được bật qua điều kiện `EnableConsumerErrorAlarms=true`.
   - `MainQueueBacklogAlarm` (`orders-queue`) mặc định tắt (`EnableBacklogAlarm=false`) để tuân thủ nguyên tắc không áp đặt ngưỡng backlog tùy tiện khi chưa đo baseline thực tế trên Lab.

---

## 3. Công cụ thu thập Metric (`scripts/collect_cloudwatch_metrics.py`)

Script [`scripts/collect_cloudwatch_metrics.py`](../scripts/collect_cloudwatch_metrics.py) hỗ trợ kiểm tra định kỳ các chỉ số vận hành và trạng thái alarm:

- **SQS Metrics (`AWS/SQS`):**
  - `ApproximateNumberOfMessagesVisible` (`Maximum`) — theo dõi backlog ở `orders-queue` và số message lỗi ở `orders-dlq`.
  - `ApproximateNumberOfMessagesNotVisible` (`Maximum`) — số message đang in-flight.
  - `ApproximateAgeOfOldestMessage` (`Maximum`).
  - `NumberOfMessagesSent`, `NumberOfMessagesReceived`, `NumberOfMessagesDeleted` (`Sum`).
- **Lambda Metrics (`AWS/Lambda`):**
  - `Invocations` (`Sum`), `Errors` (`Sum`), `Throttles` (`Sum`).
  - `Duration` (`Average`, `Maximum`), `ConcurrentExecutions` (`Maximum`).
- **Alarm State (`describe_alarms`):**
  - Ghi nhận `StateValue` (`OK`, `ALARM`, `INSUFFICIENT_DATA`) và `StateUpdatedTimestamp`.

### Cách sử dụng CLI

Chế độ kiểm tra kế hoạch offline (mặc định, không gọi AWS):

```bash
python scripts/collect_cloudwatch_metrics.py --dry-run --output-dir artifacts/metrics-dryrun
```

Chế độ truy vấn read-only trên AWS Learner Lab (do Quân thực hiện khi có phiên Lab):

```bash
python scripts/collect_cloudwatch_metrics.py \
  --region us-east-1 \
  --queues orders-queue orders-dlq \
  --functions order-producer order-consumer \
  --alarms AsyncOrderProcessing-orders-dlq-VisibleMessages \
  --window-minutes 30 \
  --period 60 \
  --execute \
  --output-dir artifacts/metrics-live
```

---
