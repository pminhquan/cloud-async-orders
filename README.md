# cloud-async-orders: Xử lý đơn hàng bất đồng bộ trên AWS

Dự án môn học sử dụng API Gateway, Lambda, SQS/DLQ, DynamoDB và CloudWatch/SNS trong AWS Learner Lab.

## 1. Tiến độ Tuần 1

SV1 đã kiểm thử SQS Standard → Consumer tại `us-east-1`: tin nhắn hợp lệ có `POC_VALIDATED`, tin nhắn lỗi được retry và chuyển DLQ. Consumer hiện chỉ kiểm tra dữ liệu và ghi log, chưa ghi DynamoDB hoặc có idempotency ở mức production. Xem [cấu hình triển khai](docs/aws-inventory.md) và [minh chứng](docs/evidence/week1/README.md).

[Sơ đồ kiến trúc Mermaid](docs/architecture/README.md) phân biệt PoC SV1, các thành phần SV2 phát triển riêng theo thông tin người dùng và các đường tích hợp tương lai. Chưa xác nhận ứng dụng E2E hoàn chỉnh.

## 2. Phân công và lộ trình

- **Quan (SV1, trưởng nhóm)**: SQS/DLQ, Consumer, kiểm thử, minh chứng SV1, sơ đồ kiến trúc và phối hợp tích hợp kỹ thuật.
- **Khôi (SV2)**: API Gateway/Producer, DynamoDB, SNS/giám sát; tổng hợp README, báo cáo tuần và khai báo AI riêng.
- Mỗi người cung cấp thông tin trung thực về đóng góp, giờ làm và việc dùng AI; Quan không duy trì báo cáo trùng. Chi tiết tại [phân công](docs/task-assignment.md).

Lộ trình: Tuần 1 nghiên cứu, kiến trúc và môi trường Lab; Tuần 2 triển khai/kiểm thử thành phần; Tuần 3 tích hợp và cảnh báo (IaC tùy chọn); Tuần 4 kiểm thử tải, chi phí, dọn Lab và demo. [Kế hoạch Tuần 1](docs/week1-plan.md) ghi rõ các bàn giao còn thiếu.

## 3. Tài liệu

- [Yêu cầu môn học và ràng buộc Lab](docs/requirements.md)
- [Kế hoạch Tuần 1](docs/week1-plan.md) · [Phân công](docs/task-assignment.md)
- [Kiến trúc](docs/architecture/README.md) · [Hợp đồng tích hợp](docs/integration-contract.md)
- [SQS Standard/FIFO và DLQ](docs/research/standard-vs-fifo.md) · [Nghiên cứu SV2](docs/research/sv2-services.md)
- [Danh mục AWS](docs/aws-inventory.md) · [Minh chứng Tuần 1](docs/evidence/week1/README.md)
- [Hoạt động và giờ làm Tuần 1](docs/worklog/week1.md)

Báo cáo tuần và khai báo AI theo yêu cầu giảng viên do Khôi tổng hợp, duy trì và nộp riêng.
