# Danh mục AWS Tuần 1

Cập nhật 2026-10-11. Kết quả SV1 dựa trên thông tin SV1 cung cấp và ảnh riêng tư tại [chỉ mục minh chứng](evidence/week1/README.md). Tên tài nguyên SV2 theo thông tin về ZIP Tuần 1 của Khôi; đây là nguồn báo cáo riêng, chưa xác nhận cấu hình chi tiết hoặc tích hợp chung tại repo.

## 1. Tài nguyên SV1 đã xác nhận

| Tên thực tế | Dịch vụ / vai trò | Trạng thái |
| :--- | :--- | :--- |
| `orders-queue` | SQS Standard, SSE-SQS; queue nguồn | Đã tạo và kiểm thử với Consumer |
| `orders-dlq` | SQS Standard, SSE-SQS; cô lập tin nhắn lỗi | Đã xác nhận body `ORD-W1-Q-ERR-002` |
| `order-processor` | Lambda Consumer kiểm tra dữ liệu và ghi log | Đã chạy trực tiếp và qua SQS; chưa ghi DynamoDB hoặc xử lý lặp an toàn cho nghiệp vụ |

| Cấu hình PoC | Giá trị |
| :--- | :--- |
| Region / execution role | `us-east-1` / `LabRole` có sẵn |
| Runtime / timeout / memory | Python 3.13 / 10 giây / 128 MB |
| Main queue visibility timeout | 60 giây |
| DLQ / redrive | `orders-dlq`; `maxReceiveCount=3`; DLQ retention 14 ngày |
| SQS trigger | Enabled |
| Batch size / batch window | 1 / 0 giây (Console hiển thị `None`) |
| Maximum concurrency của mapping | 2 |
| Report batch item failures | Disabled; exception làm thất bại cả batch |

Visibility timeout và execution role theo thông tin SV1 cung cấp; ảnh chưa mở đầy đủ hai cấu hình này. Ảnh IAM cho thấy role/trust có Lambda; invocation và ghi CloudWatch thành công không chứng minh toàn bộ quyền thực tế. Ảnh trigger Disabled là bước trước, không phải trạng thái hiện tại.

## 2. Thành phần SV2 được báo cáo riêng

API Gateway, Producer, DynamoDB và SNS dưới đây là tài nguyên triển khai riêng theo minh chứng Khôi báo cáo. CloudWatch Alarm vẫn là kế hoạch, chưa xác nhận đã triển khai. Không mặc định các thành phần này đã nối với PoC SV1.

| Thành phần Khôi phụ trách | Tên được báo cáo | Cần xác nhận thêm |
| :--- | :--- | :--- |
| API Gateway | `order-api` | Loại HTTP/REST API và kết nối Producer |
| Producer Lambda | `order-producer` | Cấu hình và luồng gửi SQS của SV1 |
| DynamoDB | `Orders` | Cấu hình khóa thực tế; khóa đích thiết kế là `orderId` |
| CloudWatch Alarm | Chưa có tên triển khai xác nhận — PLANNED | Triển khai, metric và điều kiện đánh giá |
| SNS Topic | `order-dlq-alert` | Quyền publish và xác nhận email |

Các đường tích hợp SV2 → SQS, Consumer → DynamoDB và DLQ → Alarm → SNS trên [sơ đồ](architecture/README.md) vẫn là thiết kế đích, chưa chứng minh E2E chung.

## 3. Ràng buộc Lab và việc còn thiếu

- Tags thống nhất: `Project=AsyncOrderProcessing`, `Owner=Khoi-Quan`; chưa có ảnh Tags trên từng tài nguyên.
- Không tạo IAM user/role mới; chỉ dùng `LabRole`/`LabInstanceProfile` được Lab cho phép. `LabInstanceProfile` dành cho EC2, không phải execution role Lambda; dự án không dùng EC2/EBS.
- Tổng Lambda concurrency tài khoản ≤ 10; mapping Consumer giới hạn 2 chưa chứng minh tổng sử dụng toàn tài khoản.
- Các thành phần tích hợp phải tương thích `us-east-1`. Mô hình một tài khoản chính vẫn là đề xuất; nếu khác tài khoản phải kiểm chứng quyền/chính sách cross-account. Không chia sẻ thông tin đăng nhập, access key, secret key, session token hoặc mật khẩu. Account ID là mã định danh, không phải thông tin xác thực; nên hạn chế thông tin cá nhân và mã định danh không cần thiết khi công khai minh chứng.
