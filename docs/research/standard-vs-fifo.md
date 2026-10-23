# Nghiên cứu & Thiết kế Kiểm thử SQS Standard vs FIFO (Cập nhật Tuần 3)

## 1. So sánh kỹ thuật chuyên sâu

| Tiêu chí | Amazon SQS Standard | Amazon SQS FIFO |
|---|---|---|
| **Hậu tố tên Queue** | Không dùng `.fifo` (ví dụ: `orders-queue`, `orders-benchmark-standard`) | Bắt buộc kết thúc bằng `.fifo` (ví dụ: `orders-benchmark.fifo`) |
| **Thứ tự (Ordering)** | **Best-effort ordering:** có thể xảy ra nhận lệch thứ tự (out-of-order) khi nhiều worker/partition xử lý song song | **Order-preserving per group:** giữ thứ tự nghiêm ngặt trong phạm vi từng `MessageGroupId`; **không** ép thứ tự toàn cục giữa các `MessageGroupId` khác nhau |
| **Cơ chế phân phối & chống gửi trùng** | **At-least-once delivery:** một message có thể được phân phối hơn 1 lần | **Exactly-once processing semantics (trong cửa sổ 5 phút):** chặn gửi trùng ở tầng Producer bằng `MessageDeduplicationId` hoặc `ContentBasedDeduplication` trong 5 phút |
| **Thông lượng (Throughput)** | Gần như không giới hạn theo thiết kế dịch vụ | Phụ thuộc số lượng `MessageGroupId` đang hoạt động và chế độ throughput của Region |
| **Dead Letter Queue (DLQ)** | Phải là Standard Queue (`orders-dlq`) | Phải là FIFO Queue (`.fifo`); khi một message trong group bị lỗi và retry/chuyển DLQ, các message cùng `MessageGroupId` phía sau bị chặn hoặc ảnh hưởng thứ tự |
| **Yêu cầu Idempotency ở Consumer** | **Bắt buộc** (`attribute_not_exists(orderId)`) | **Vẫn bắt buộc:** deduplication 5 phút của FIFO chỉ chặn gửi lặp vào SQS, không ngăn được việc Consumer đã ghi DynamoDB nhưng gặp lỗi/timeout trước khi xóa message khỏi SQS |

Nguồn tham khảo chính thức từ AWS:
- [SQS Standard Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)
- [SQS FIFO Queue Logic & MessageGroupId](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html)
- [SQS FIFO Deduplication](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)
- [SQS Dead-Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)

---

## 2. Những ngộ nhận cần tránh khi phân tích kết quả Benchmark

1. **Không kết luận Standard "luôn tạo duplicate" hoặc "không bao giờ tạo duplicate" chỉ từ một lần chạy mẫu nhỏ:**
   - Ở tải nhỏ (20–50 messages), Standard queue thường trả về `0` duplicate và thứ tự gần như tuần tự. Điều đó không có nghĩa Standard cam kết FIFO hay exactly-once; vì vậy tầng Consumer của dự án vẫn bắt buộc duy trì conditional write `attribute_not_exists(orderId)`.
2. **Không kết luận FIFO bảo đảm thứ tự toàn cục (global ordering) khi dùng nhiều `MessageGroupId`:**
   - Khi chạy `--group-count 4`, các message có cùng `MessageGroupId` luôn tăng dần theo `sequenceNumber`, nhưng thứ tự nhận tổng thể giữa `bench-group-01` và `bench-group-02` sẽ đan xen nhau. Vì vậy công cụ `scripts/benchmark_sqs.py` đánh giá ordering **theo từng group (`perGroup`)** và tách riêng kịch bản `single-group` (`group_count=1`) với `multi-group` (`group_count>1`).
3. **Không suy diễn số lần retry chính xác từ CloudWatch `ApproximateNumberOfMessagesVisible`:**
   - Các metric `Approximate*` của SQS là xấp xỉ theo chu kỳ lấy mẫu; số lần xử lý thực tế phải đối chiếu với `ApproximateReceiveCount` trên message và log thực thi của Lambda.

---

## 3. Lộ trình áp dụng qua 3 tuần trong dự án `cloud-async-orders`

- **Tuần 1:** Nghiên cứu lý thuyết Standard/FIFO và dựng PoC trên `orders-queue` (SQS Standard) + `orders-dlq`.
- **Tuần 2:** Hoàn thiện luồng tích hợp chính trên SQS Standard kèm **Consumer Idempotency (`attribute_not_exists(orderId)`)** và phát hiện xung đột `ORDER_CONFLICT`.
- **Tuần 3:** Xây dựng công cụ [`scripts/benchmark_sqs.py`](../../scripts/benchmark_sqs.py) và [`scripts/generate_week3_report.py`](../../scripts/generate_week3_report.py) để thực hiện phép đo đối chứng giữa:
  1. `Standard Queue` (`orders-benchmark-standard`)
  2. `FIFO Single-Group` (`orders-benchmark.fifo`, `--group-count 1`)
  3. `FIFO Multi-Group` (`orders-benchmark.fifo`, `--group-count 4`)
  mà **không thay đổi** Producer/Consumer production đang vận hành ổn định trên `orders-queue`.
