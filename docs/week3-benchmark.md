# Thiết kế & Hướng dẫn Benchmark SQS Standard vs FIFO (W3-02)

## 1. Mục tiêu và phạm vi

Công cụ [`scripts/benchmark_sqs.py`](../scripts/benchmark_sqs.py) được thiết kế để đo lường và so sánh thực nghiệm giữa **Amazon SQS Standard Queue** và **Amazon SQS FIFO Queue** trên môi trường AWS Learner Lab mà không làm ảnh hưởng đến luồng đơn hàng chính (`orders-queue` và `orders-dlq`).

### Phân tách phạm vi benchmark

1. **SQS API Benchmark (`scripts/benchmark_sqs.py` — W3-02):**
   - Đo trực tiếp thao tác `SendMessage` / `SendMessageBatch` và vòng lặp `ReceiveMessage` / `DeleteMessage` trên hai queue thử nghiệm riêng (`orders-benchmark-standard` và `orders-benchmark.fifo`).
   - Đánh giá thông lượng gửi/nhận, độ trễ API (`mean`, `median`, `p95`), tỉ lệ nhận đủ (`receiveCompletenessRatio`), quan sát gửi lặp (`duplicateObservations`) và thứ tự nhận (`ordering`).
2. **Full Pipeline E2E Benchmark (`scripts/load_test_orders.py` — W3-03):**
   - Đo luồng `API Gateway → Producer → SQS → Consumer → DynamoDB` và đối soát trạng thái `status = PROCESSED` bằng `GetItem`.
   - Không đánh đồng độ trễ `ReceiveMessage` của SQS với thời gian hoàn tất xử lý đơn hàng ở Consumer/DynamoDB.

---

## 2. Cơ chế an toàn (Safety Guardrails)

- **Chặn tuyệt đối queue production:** Nếu người dùng truyền `orders-queue`, `orders-dlq`, `orders-queue.fifo`, hoặc `orders-dlq.fifo` (dù ở dạng tên hay Queue URL), script lập tức từ chối thực thi với `BenchmarkError`.
- **Mặc định `--dry-run`:** Không phát sinh bất kỳ cuộc gọi AWS nào nếu thiếu đồng thời hai tham số `--execute` và `--confirm-target <exact-queue-name>`.
- **Không tự tạo/xóa/purge queue:** Script chỉ gửi message có gắn `benchmarkRunId` của lần chạy hiện tại và chỉ xóa đúng những message khớp `benchmarkRunId` đó trong vòng lặp nhận có giới hạn (`--max-polls`, `--timeout`).

---

## 3. Các chỉ số đo lường & Ngữ nghĩa FIFO

### 3.1. Danh mục chỉ số xuất ra (`benchmark-summary.json` & `benchmark-results.csv`)
- `attemptedMessages`, `acceptedSends`, `failedSends`.
- `uniqueReceivedMessages`: số lượng `orderId` duy nhất nhận được. Nếu cùng một `orderId` được SQS phân phối lại (redelivery/at-least-once), script ghi nhận vào `duplicateObservations` chứ **không** cộng dồn làm sai lệch `uniqueReceivedMessages`.
- `receiveCompletenessRatio`: `uniqueReceivedMessages / acceptedSends`.
- `sendLatencyMs` và `receivePollLatencyMs`: thống kê `count`, `minMs`, `maxMs`, `meanMs`, `medianMs`, `p95Ms`.
- `sendThroughputMsgPerSec` và `receiveThroughputMsgPerSec`.
- `ordering`: kiểm tra thứ tự `sequenceNumber` theo từng `MessageGroupId` (`perGroup`) và tổng số lần nghịch đảo thứ tự (`outOfOrderTransitions`).

### 3.2. Ngữ nghĩa FIFO Queue
- Tên queue FIFO bắt buộc kết thúc bằng hậu tố `.fifo`.
- Mỗi message gửi vào FIFO có `MessageGroupId` và `MessageDeduplicationId` (khi `--dedup-mode explicit`) hoặc dựa trên hash nội dung (khi `--dedup-mode content-based`).
- **Single-group (`--group-count 1`) vs Multi-group (`--group-count > 1`):**
  - `Single-group`: toàn bộ message đi vào cùng một `MessageGroupId`, bảo đảm tuần tự tuyệt đối từ đầu đến cuối nhưng giới hạn mức độ song song.
  - `Multi-group`: phân bổ message qua nhiều `MessageGroupId` (ví dụ theo `customerId`); thứ tự được bảo toàn nghiêm ngặt **bên trong từng group**, trong khi các group khác nhau có thể đan xen nhau để tăng thông lượng.

---

## 4. Lệnh chạy mẫu

### 4.1. Kiểm tra Dry-run Offline (không cần AWS credentials)

```bash
python scripts/benchmark_sqs.py \
  --queue-type standard \
  --queue-url orders-benchmark-standard \
  --message-count 20 \
  --dry-run \
  --output-dir artifacts/bench-dryrun-std

python scripts/benchmark_sqs.py \
  --queue-type fifo \
  --queue-url orders-benchmark.fifo \
  --message-count 20 \
  --group-count 4 \
  --dry-run \
  --output-dir artifacts/bench-dryrun-fifo
```

### 4.2. Tổng hợp bảng Markdown bằng Report Generator

```bash
python scripts/generate_week3_report.py \
  --benchmark-json artifacts/bench-dryrun-std/benchmark-summary.json artifacts/bench-dryrun-fifo/benchmark-summary.json \
  --synthetic-sample \
  --output artifacts/sample-benchmark-report.md
```

---

## Giới hạn gọi API và quan sát

`--timeout` là ngân sách vòng nhận sau giai đoạn gửi; `--max-polls` giới hạn số lần receive. Công cụ kiểm tra hạn trước mỗi receive và trước delete từng message; chỉ message khớp runId, orderId và SQS MessageId đã gửi thành công mới được xử lý. SDK dùng một tổng lần thử cho mỗi call, không tự retry.

Call đang chạy chịu connect/read timeout hữu hạn lấy từ cấu hình; ngân sách vòng lặp không cưỡng bức hủy một request mạng đã bắt đầu. Send latency và receive polling latency là số đo API SQS, không phải thời gian Consumer/DynamoDB hoàn tất.


Report generator chỉ xuất các phần có JSON đầu vào. Giá trị số thiếu được hiển thị bằng dấu “—”; số 0 được giữ khi thực sự có trong dữ liệu. Không tự tạo bảng so sánh hoặc trạng thái tiến độ cho phần không có input.
