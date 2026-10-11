# cloud-async-orders: Xử lý đơn hàng bất đồng bộ trên AWS

Dự án môn học sử dụng API Gateway, Lambda, SQS/DLQ, DynamoDB và CloudWatch/SNS trong AWS Learner Lab.

## 1. Tiến độ Tuần 1

SV1 đã kiểm thử SQS Standard → Consumer tại `us-east-1`: tin nhắn hợp lệ có `POC_VALIDATED`, tin nhắn lỗi được retry và chuyển DLQ. Consumer hiện chỉ kiểm tra dữ liệu và ghi log, chưa ghi DynamoDB hoặc có idempotency ở mức production. Xem [cấu hình triển khai](docs/aws-inventory.md) và [minh chứng](docs/evidence/week1/README.md).

SV2 đã kiểm thử API Gateway → Producer trả `202`, tạo DynamoDB `Orders` và SNS `order-dlq-alert` với email subscription `Confirmed`. Producer chưa gửi SQS; CloudWatch Alarm vẫn là kế hoạch.

Ba PR Tuần 1 đã merge vào `main`, gồm mã [Consumer](src/consumer/lambda_function.py), [Producer](src/producer/lambda_function.py), 8 Consumer unit tests và 32 ảnh minh chứng (26 SV1, 6 SV2). Hai PoC được kiểm thử riêng; chưa tích hợp E2E. [Sơ đồ Mermaid](docs/architecture/README.md) phân biệt các thành phần đã triển khai và luồng tương lai.

## 2. Phân công và lộ trình

- **Quan (SV1, trưởng nhóm)**: SQS/DLQ, Consumer, kiểm thử, minh chứng SV1, sơ đồ kiến trúc và phối hợp tích hợp kỹ thuật.
- **Khôi (SV2)**: API Gateway/Producer, DynamoDB, SNS/giám sát; tổng hợp README, báo cáo tuần và khai báo AI riêng.
- Mỗi người cung cấp thông tin trung thực về đóng góp, giờ làm và việc dùng AI; Quan không duy trì báo cáo trùng. Chi tiết tại [phân công](docs/task-assignment.md).

Lộ trình: Tuần 1 nghiên cứu, kiến trúc, môi trường Lab và hai PoC riêng; Tuần 2 tích hợp Producer → SQS → Consumer → DynamoDB; Tuần 3 hoàn thiện cảnh báo (IaC tùy chọn); Tuần 4 kiểm thử tải, chi phí, dọn Lab và demo. [Kế hoạch Tuần 1](docs/week1-plan.md) phân biệt phần kỹ thuật đã hoàn thành và các mục hành chính còn chờ.

## 3. Tài liệu

- [Yêu cầu môn học và ràng buộc Lab](docs/requirements.md)
- [Kế hoạch Tuần 1](docs/week1-plan.md) · [Phân công](docs/task-assignment.md)
- [Kiến trúc](docs/architecture/README.md) · [Hợp đồng tích hợp](docs/integration-contract.md)
- [SQS Standard/FIFO và DLQ](docs/research/standard-vs-fifo.md) · [Nghiên cứu SV2](docs/research/sv2-services.md)
- [Danh mục AWS](docs/aws-inventory.md) · [Minh chứng Tuần 1](docs/evidence/week1/README.md)
- [Hoạt động và giờ làm Tuần 1](docs/worklog/week1.md)

Báo cáo tuần và khai báo AI theo yêu cầu giảng viên do Khôi tổng hợp, duy trì và nộp riêng; việc nộp vẫn chờ xác nhận.
