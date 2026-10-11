# Nhật ký hoạt động Tuần 1

Mỗi sinh viên phải ghi ít nhất **8 giờ thực tế/tuần**. Khôi tổng hợp báo cáo tiến độ riêng; Quan chỉ cung cấp và xác nhận phần việc của mình. Không tính timestamp log/ảnh hoặc thời gian AI thực thi thành giờ làm.

## 1. SV1 — Quan

| Hoạt động đã hoàn thành | Minh chứng trong repo |
| :--- | :--- |
| Nghiên cứu SQS Standard/FIFO và DLQ; ghi tài liệu kỹ thuật SV1 | [Nghiên cứu SV1](../research/standard-vs-fifo.md) |
| Cấu hình SQS Standard `orders-queue`, `orders-dlq`, Consumer `order-processor` và trigger | [W1-Q-CONFIG](../evidence/week1/README.md#w1-q-config) |
| Test Lambda trực tiếp: valid thành công; quantity sai sinh `INVALID_SCHEMA` | [W1-Q-DIRECT](../evidence/week1/README.md#w1-q-direct) |
| Qua SQS: `ORD-W1-Q-003` có `POC_VALIDATED`; `ORD-W1-Q-ERR-002` có lỗi lặp và body trong DLQ | [W1-Q-E2E](../evidence/week1/README.md#w1-q-e2e) |
| Lưu mã nguồn Consumer PoC, 8 unit tests và 26 ảnh AWS SV1 | [Consumer](../../src/consumer/lambda_function.py), [tests](../../tests/test_consumer.py), [ảnh SV1](../evidence/week1/README.md#3-chỉ-mục-26-ảnh-sv1) |
| Hoàn thành sơ đồ kiến trúc, phân biệt PoC riêng và luồng tích hợp tương lai | [Sơ đồ Mermaid](../architecture/README.md) |

## 2. SV2 — Khôi

| Hoạt động đã hoàn thành | Minh chứng trong repo |
| :--- | :--- |
| Nghiên cứu API Gateway, Lambda, DynamoDB và SNS | [Nghiên cứu SV2](../research/sv2-services.md) |
| Tạo `order-api`, route `POST /orders` và Producer `order-producer`; test Lambda/API trả `202`, đơn hàng `PENDING` | [Báo cáo SV2](../sv2-week1.md), [Producer](../../src/producer/lambda_function.py) |
| Tạo bảng `Orders` (partition key `orderId`, On-demand), SNS `order-dlq-alert` và email subscription `Confirmed` | [6 ảnh SV2](../evidence/week1/README.md#4-minh-chứng-sv2--6-ảnh) |
| Cung cấp mã nguồn, dữ liệu test, minh chứng và nội dung báo cáo SV2 để tổng hợp tài liệu nhóm | [README gốc SV2](../sv2-original-README.md), [báo cáo SV2](../sv2-week1.md) |

Producer và Consumer đã được kiểm thử riêng; Producer chưa gửi SQS, Consumer chưa ghi DynamoDB. Tích hợp E2E thuộc Tuần 2; CloudWatch Alarm vẫn là kế hoạch.

## 3. Giờ làm và báo cáo tuần

Theo khai báo của nhóm, **Quan và Khôi đều đã đạt tối thiểu 8 giờ làm thực tế trong Tuần 1**. Đây là thông tin tự khai báo, chưa được xác minh độc lập. Chưa có ngày làm cụ thể, giờ bắt đầu/kết thúc, tổng giờ chính xác hoặc phân bổ giờ theo hoạt động; các hoạt động và ảnh trên không thay thế bảng giờ làm.

Khôi tổng hợp và nộp riêng báo cáo tuần cùng khai báo AI; mỗi người cung cấp thông tin trung thực về phần việc của mình. Việc nộp hai báo cáo vẫn chờ xác nhận, không được coi là đã hoàn tất chỉ vì mã nguồn và minh chứng đã có trong repo.
