# Kế hoạch Tuần 1

Mục tiêu: hoàn thành nghiên cứu AWS, tài liệu nền tảng, sơ đồ kiến trúc, kiểm tra môi trường Lab và ghi nhận giờ làm/minh chứng theo [yêu cầu dự án](requirements.md).

## 1. Nhiệm vụ và trạng thái

| Mã | Nhiệm vụ / bàn giao | Phụ trách | Trạng thái và minh chứng |
| :--- | :--- | :--- | :--- |
| **W1-T01** | README, yêu cầu, phân công, hợp đồng và danh mục AWS | Khôi tổng hợp; Quan cung cấp phần SV1 | Có tài liệu trong working tree; chờ sinh viên duyệt. |
| **W1-T02a** | Nghiên cứu SQS Standard/FIFO và DLQ | Quan | [Nghiên cứu SV1](research/standard-vs-fifo.md), có kết quả PoC. |
| **W1-T02b** | Nghiên cứu API Gateway, DynamoDB, SNS, retry/alerting | Khôi | [Nghiên cứu SV2](research/sv2-services.md); triển khai SV2 được báo cáo riêng. |
| **W1-T03** | Sơ đồ đủ thành phần, luồng chính/lỗi và trách nhiệm | Quan; Khôi góp ý SV2 | Đã có [sơ đồ Mermaid](architecture/README.md); chờ sinh viên rà soát và nộp. |
| **W1-T04** | Kiểm tra Lab, Region, `LabRole` và tương thích tài khoản | Cả hai | [Minh chứng PoC](evidence/week1/README.md): `us-east-1`, role tồn tại và invocation thành công; quyền đầy đủ/mô hình tích hợp tài khoản còn chờ xác nhận. |
| **W1-T05** | Quy ước và kiểm tra tags | Cả hai | `Project=AsyncOrderProcessing`, `Owner=Khoi-Quan` theo người dùng; còn thiếu ảnh Tags từng tài nguyên. |
| **W1-T06** | Hoạt động, giờ làm và minh chứng (≥ 8 giờ/người) | Mỗi người cung cấp; Khôi tổng hợp riêng | [Nhật ký](worklog/week1.md) có hoạt động SV1; thời lượng thực tế chưa xác minh. |
| **W1-T07** | Khai báo AI theo yêu cầu giảng viên | Khôi tổng hợp/nộp riêng; Quan xác nhận phần mình | Người dùng xác nhận đã chuẩn bị riêng; nội dung và việc nộp không được đối soát tại repo. |

## 2. Ràng buộc và phạm vi

Chỉ dùng role/profile Lab cho phép (`LabRole`/`LabInstanceProfile`), không tạo IAM user/role mới; tổng Lambda concurrency toàn tài khoản ≤ 10. Chỉ gắn/kiểm tra tags trên tài nguyên được phép tạo, không tạo tài nguyên rác để chụp ảnh.

PoC sớm đã xác nhận Consumer validate/log và retry/DLQ; xem [cấu hình](aws-inventory.md). Không suy ra giảng viên đã duyệt prototype sớm nếu chưa có xác nhận. Producer → SQS → Consumer → DynamoDB, idempotency và cảnh báo tích hợp thuộc giai đoạn sau. Tuần 1 chưa hoàn tất khi giờ làm và các minh chứng còn thiếu.
