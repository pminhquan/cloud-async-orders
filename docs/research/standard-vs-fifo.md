# Nghiên cứu SQS Standard và FIFO

## 1. SQS Standard

Đặc điểm phù hợp với đề tài:
- throughput cao;
- delivery at-least-once;
- có thể có duplicate;
- thứ tự không đảm bảo tuyệt đối.

Vì vậy Consumer phải có idempotency theo `orderId`.

## 2. SQS FIFO

Đặc điểm:
- duy trì thứ tự trong message group;
- hỗ trợ deduplication;
- tên queue phải có hậu tố `.fifo`;
- source queue và DLQ phải cùng loại khi cấu hình redrive.

## 3. Áp dụng trong dự án

Tuần 1:
- nghiên cứu Standard/FIFO;
- PoC chính dùng Standard.

Tuần 2:
- luồng tích hợp/Retry-DLQ và load nhỏ tập trung Standard queue;
- idempotency được hoàn thiện ở Consumer để xử lý khả năng duplicate.

Giai đoạn sau:
- tạo/kiểm thử FIFO có kiểm soát;
- đo/so sánh ordering, duplicate behavior, throughput và cấu hình message group/deduplication;
- không kết luận Standard/FIFO chỉ từ lý thuyết nếu chưa có benchmark thực tế.

## 4. Tiêu chí so sánh dự kiến

| Tiêu chí | Standard | FIFO |
|---|---|---|
| Ordering | Best-effort | Theo message group |
| Duplicate | Có thể | Có cơ chế deduplication |
| Throughput | Cao | Có giới hạn/cơ chế riêng |
| Độ phức tạp Producer | Thấp | Cần group/dedup config |
| Idempotency Consumer | Vẫn cần | Vẫn nên có |

## 5. Kết luận tạm

Standard phù hợp để kiểm thử pipeline bất đồng bộ ban đầu. FIFO là nhánh so sánh của đề tài, cần benchmark riêng ở tuần sau.
