# AWS Manual Runbook — Hướng dẫn Thao tác & Nghiệm thu Tuần 3 trên AWS Learner Lab

> **Tài liệu dành riêng cho Phạm Minh Quân và Nguyễn Đoàn Minh Khôi khi mở phiên AWS Learner Lab.**
> - Toàn bộ công cụ và unit tests offline đã được hoàn tất và kiểm chứng (`IMPLEMENTED + LOCAL VERIFIED`).
> - Tài liệu này phân biệt rõ các thao tác **[READ-ONLY]** (chỉ đọc, không làm thay đổi trạng thái tài nguyên) và **[WRITE / CONTROLLED TEST]** (có tạo tài nguyên giám sát hoặc gửi message kiểm thử có giới hạn).
> - **Nguyên tắc an toàn tuyệt đối:**
>   1. Không tạo IAM User hoặc IAM Role mới; chỉ dùng `LabRole` có sẵn.
>   2. Không chạy `PurgeQueue` hoặc xóa dữ liệu trong bảng DynamoDB `Orders`.
>   3. Không dùng `orders-queue` hoặc `orders-dlq` làm mục tiêu chạy `scripts/benchmark_sqs.py`.
>   4. Không vượt giới hạn tổng Lambda concurrency `<= 10` của tài khoản Learner Lab.

---

## Bước 1 — Kiểm tra Tài nguyên Hiện có `[READ-ONLY]`

**Mục đích:** Xác nhận trạng thái các tài nguyên từ Tuần 2 trước khi chạy thử nghiệm Tuần 3.
**Tác động & Rủi ro:** Không làm thay đổi cấu hình hay dữ liệu.

```bash
export AWS_DEFAULT_REGION=us-east-1

# 1. Kiểm tra danh sách SQS queues
aws sqs list-queues --region us-east-1

# 2. Kiểm tra bảng DynamoDB Orders
aws dynamodb describe-table --table-name Orders --region us-east-1 --query "Table.{Name:TableName,Status:TableStatus}"

# 3. Kiểm tra 2 hàm Lambda
aws lambda get-function-configuration --function-name order-producer --region us-east-1 --query "{Name:FunctionName,State:State,Role:Role}"
aws lambda get-function-configuration --function-name order-consumer --region us-east-1 --query "{Name:FunctionName,State:State,Role:Role}"

# 4. Lấy ARN của SNS Topic order-dlq-alert (Khôi & Quân đối soát)
aws sns list-topics --region us-east-1
```

- **Khôi thực hiện:** Mở AWS Console → Amazon SNS → Topics → `order-dlq-alert` → kiểm tra Email Subscription đang ở trạng thái `Confirmed`. Chụp ảnh `W3-SNS-Topic-Subscription-Confirmed.png` (nhớ che địa chỉ email cá nhân).

---

## Bước 2 — Triển khai CloudWatch Alarm kết nối SNS `[WRITE - MONITORING ONLY]`

**Mục đích:** Triển khai `DLQVisibleMessagesAlarm` theo dõi `orders-dlq` (`ApproximateNumberOfMessagesVisible >= 1`) và gắn `AlarmActions` vào ARN của `order-dlq-alert`.
**Tác động & Rủi ro:** Chỉ tạo CloudWatch Alarm; không tạo IAM Role, không tạo trùng SNS Topic, không chạm vào Lambda hay SQS trigger.

### Cách A — Triển khai bằng CloudFormation (`iac/week3-monitoring.yaml`)

```bash
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name async-orders-week3-monitoring \
  --template-file iac/week3-monitoring.yaml \
  --parameter-overrides \
      AWSRegionName=us-east-1 \
      MainQueueName=orders-queue \
      DLQName=orders-dlq \
      ConsumerFunctionName=order-consumer \
      AlertSnsTopicArn=arn:aws:sns:us-east-1:<ACCOUNT_ID>:order-dlq-alert \
      DLQAlarmThreshold=1 \
      DLQEvaluationPeriods=1 \
      AlarmPeriodSeconds=60 \
      EnableConsumerErrorAlarms=true \
      EnableBacklogAlarm=false
```

### Cách B — Lệnh AWS CLI trực tiếp (Dự phòng nếu quyền CloudFormation trên Lab bị giới hạn)

```bash
aws cloudwatch put-metric-alarm \
  --region us-east-1 \
  --alarm-name "AsyncOrderProcessing-orders-dlq-VisibleMessages" \
  --alarm-description "Triggers when orders-dlq has >= 1 visible message" \
  --namespace "AWS/SQS" \
  --metric-name "ApproximateNumberOfMessagesVisible" \
  --dimensions Name=QueueName,Value=orders-dlq \
  --statistic Maximum \
  --period 60 \
  --evaluation-periods 1 \
  --datapoints-to-alarm 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "arn:aws:sns:us-east-1:<ACCOUNT_ID>:order-dlq-alert" \
  --ok-actions "arn:aws:sns:us-east-1:<ACCOUNT_ID>:order-dlq-alert"
```

- Chụp ảnh cấu hình Alarm ở trạng thái `OK`: `W3-CW-DLQ-Alarm-Config-OK.png`.

---

## Bước 3 — Kiểm thử Kích hoạt Cảnh báo `DLQ → Alarm → SNS → Email` `[WRITE - CONTROLLED ALERT TEST]`

**Mục đích:** Xác minh khi có message lỗi chuyển sang `orders-dlq` (hoặc khi đặt thử trạng thái alarm), CloudWatch kích hoạt SNS và gửi email thành công.
**Tác động & Rủi ro:** Không gửi trực tiếp dữ liệu rác vào `orders-dlq`. Có 2 phương án an toàn:
1. **Phương án 1 (Quan sát từ message lỗi qua luồng retry chuẩn):** Nếu `orders-dlq` đang có sẵn `>= 1` message lỗi từ bài test `INVALID_JSON` hoặc chỉ khi owner duyệt riêng kịch bản, gửi tối đa 1 message thử sai định dạng qua `orders-queue` để quan sát redrive. Không làm khi có đơn thật chưa được cô lập; không suy số lần Lambda invocation chính xác từ receive count.
2. **Phương án 2 (Kiểm tra liên kết Alarm → SNS không làm bẩn queue):** Dùng `aws cloudwatch set-alarm-state` để kiểm tra đường truyền SNS email trước, sau đó kiểm tra bằng metric thật từ `orders-dlq`.

```bash
# Kiểm tra trạng thái Alarm hiện tại [READ-ONLY]
aws cloudwatch describe-alarms \
  --region us-east-1 \
  --alarm-names "AsyncOrderProcessing-orders-dlq-VisibleMessages"
```

- **Quân chụp:** `W3-CW-DLQ-Alarm-Triggered-ALARM.png` (màn hình CloudWatch Alarm ở trạng thái `In alarm`).
- **Khôi chụp:** `W3-SNS-Email-Notification-Received.png` (email cảnh báo nhận được từ AWS Notifications, che thông tin cá nhân/Account ID).

---

## Bước 4 — Chạy Benchmark SQS Standard vs FIFO trên Queue Thử nghiệm Riêng `[WRITE - ISOLATED BENCHMARK QUEUES]`

**Mục đích:** Đo thông lượng, độ trễ (`mean`, `median`, `p95`), tỉ lệ nhận đủ và tính chất thứ tự (`ordering`) giữa Standard, FIFO Single-Group và FIFO Multi-Group.
**Tác động & Rủi ro:** Thực hiện hoàn toàn trên 2 queue thử nghiệm độc lập (`orders-benchmark-standard` và `orders-benchmark.fifo`). Tuyệt đối **không chạm vào `orders-queue` hay `orders-dlq`**.

### 4.1. Cấp queue thử nghiệm (chỉ khi người thao tác được cho phép tạo)

Ưu tiên queue thử đã được cấp. Các lệnh dưới đây là WRITE, tạo tài nguyên có chi phí; chỉ người thao tác đã được owner cho phép mới chạy sau khi kiểm tra queue chưa tồn tại. Agent không chạy chúng trong phiên offline.

```bash
# 1. Tạo Standard benchmark queue
aws sqs create-queue \
  --region us-east-1 \
  --queue-name orders-benchmark-standard \
  --tags Project=AsyncOrderProcessing,Owner=Khoi-Quan

# 2. Tạo FIFO benchmark queue
aws sqs create-queue \
  --region us-east-1 \
  --queue-name orders-benchmark.fifo \
  --attributes FifoQueue=true,ContentBasedDeduplication=false \
  --tags Project=AsyncOrderProcessing,Owner=Khoi-Quan
```

- Chụp ảnh danh sách 2 queue thử nghiệm: `W3-Bench-Queues-Isolated-Created.png`.

### 4.2. Chạy 3 kịch bản Benchmark bằng `scripts/benchmark_sqs.py`

```bash
# Kịch bản 1: Standard Queue (50 messages, batch=1)
python scripts/benchmark_sqs.py \
  --queue-type standard \
  --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/orders-benchmark-standard \
  --message-count 50 \
  --batch-size 1 \
  --rate 25 \
  --timeout 20 \
  --max-polls 40 \
  --execute \
  --confirm-target orders-benchmark-standard \
  --output-dir artifacts/live-bench-standard

# Kịch bản 2: FIFO Queue — Single Group (group-count = 1)
python scripts/benchmark_sqs.py \
  --queue-type fifo \
  --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/orders-benchmark.fifo \
  --message-count 50 \
  --batch-size 1 \
  --group-count 1 \
  --dedup-mode explicit \
  --rate 25 \
  --timeout 20 \
  --max-polls 40 \
  --execute \
  --confirm-target orders-benchmark.fifo \
  --output-dir artifacts/live-bench-fifo-single

# Kịch bản 3: FIFO Queue — Multi Group (group-count = 5)
python scripts/benchmark_sqs.py \
  --queue-type fifo \
  --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/orders-benchmark.fifo \
  --message-count 50 \
  --batch-size 1 \
  --group-count 5 \
  --dedup-mode explicit \
  --rate 25 \
  --timeout 20 \
  --max-polls 40 \
  --execute \
  --confirm-target orders-benchmark.fifo \
  --output-dir artifacts/live-bench-fifo-multi
```

- Chụp 3 ảnh kết quả CLI: `W3-Bench-Standard-CLI-Summary.png`, `W3-Bench-FIFO-SingleGroup-CLI-Summary.png`, `W3-Bench-FIFO-MultiGroup-CLI-Summary.png`.

---

## Bước 5 — Chạy Kiểm thử Tải Có Kiểm soát & Đối soát DynamoDB `[WRITE API / READ-ONLY DYNAMODB]`

**Mục đích:** Gửi 20 request hợp lệ tới `POST /orders` ở tốc độ an toàn (`2 req/s`, tuân thủ concurrency `<= 10`) và đối soát toàn bộ 20 `orderId` đạt `status = PROCESSED` trong bảng `Orders` bằng `GetItem`.
**Tác động & Rủi ro:** Tạo 20 bản ghi đơn hàng thử nghiệm có prefix `CUS-LOAD-W3` trong bảng `Orders`. Phần đối soát DynamoDB chỉ dùng `GetItem` (read-only), không `Scan` và không xóa dữ liệu.

```bash
python scripts/load_test_orders.py \
  --endpoint https://<API_ID>.execute-api.us-east-1.amazonaws.com/orders \
  --count 20 \
  --rate 2.0 \
  --timeout 5.0 \
  --customer-prefix CUS-LOAD-W3 \
  --table-name Orders \
  --region us-east-1 \
  --reconcile-timeout 30 \
  --reconcile-max-polls 8 \
  --execute \
  --confirm-target <API_ID>.execute-api.us-east-1.amazonaws.com \
  --output-dir artifacts/live-load-test
```

- Chụp ảnh kết quả: `W3-Load-API-And-DynamoDB-Reconciliation.png`.

---

## Bước 6 — Thu thập CloudWatch Metrics & Tổng hợp Báo cáo `[READ-ONLY]`

**Mục đích:** Lấy số liệu CloudWatch thực tế của `orders-queue`, `orders-dlq`, `order-producer`, `order-consumer` và trạng thái Alarm trong 30 phút vừa chạy test, sau đó xuất bảng tổng hợp Markdown.

```bash
# 1. Thu thập CloudWatch metrics [READ-ONLY]
python scripts/collect_cloudwatch_metrics.py \
  --region us-east-1 \
  --queues orders-queue orders-dlq \
  --functions order-producer order-consumer \
  --alarms AsyncOrderProcessing-orders-dlq-VisibleMessages \
  --window-minutes 30 \
  --period 60 \
  --execute \
  --output-dir artifacts/live-cloudwatch

# 2. Sinh báo cáo tổng hợp Markdown từ kết quả thật
python scripts/generate_week3_report.py \
  --benchmark-json \
      artifacts/live-bench-standard/benchmark-summary.json \
      artifacts/live-bench-fifo-single/benchmark-summary.json \
      artifacts/live-bench-fifo-multi/benchmark-summary.json \
  --load-json artifacts/live-load-test/load-test-summary.json \
  --cloudwatch-json artifacts/live-cloudwatch/cloudwatch-metrics-summary.json \
  --output artifacts/week3-measured-summary.md
```

- Chụp ảnh kết quả: `W3-Metrics-Collector-CloudWatch-Summary.png`.

---

## Bước 7 — Dọn dẹp An toàn sau Phiên Benchmark (Tùy chọn) `[WRITE - TEST QUEUES ONLY]`

- Không thực hiện cleanup trong phiên offline này. Sau này chỉ xóa queue thử khi owner cho phép riêng, đã xác minh chính xác queue và không còn dữ liệu cần giữ. Không purge queue.
- **Tuyệt đối KHÔNG được làm:** Không xóa `orders-queue`, `orders-dlq`, `order-producer`, `order-consumer`, bảng `Orders`, SNS `order-dlq-alert` hoặc `DLQVisibleMessagesAlarm`.
