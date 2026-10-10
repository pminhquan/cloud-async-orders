# cloud-async-orders: Hệ Thống Xử Lý Đơn Hàng Bất Đồng Bộ (AWS Serverless)

Dự án môn học xây dựng hệ thống xử lý đơn hàng bất đồng bộ (Asynchronous Order Processing) trên AWS Serverless, hướng đến tính sẵn sàng cao, chịu lỗi và tối ưu chi phí trong môi trường AWS Learner Lab.

## 1. Tổng Quan Kiến Trúc

Luồng xử lý chính:
`API Gateway -> Producer Lambda (order-producer) -> SQS Queue -> Consumer Lambda (order-processor) -> DynamoDB (Orders)`

- **Amazon API Gateway**: Nhận yêu cầu `POST /orders`, chuyển tiếp đến Producer Lambda.
- **AWS Lambda (`order-producer`)**: Validate dữ liệu cơ bản, gửi tin nhắn vào SQS, phản hồi `202 Accepted` khi gửi thành công.
- **Amazon SQS (`orders-queue` & `orders-dlq`)**: Đệm tin nhắn đơn hàng; cô lập tin nhắn lỗi vào DLQ sau ngưỡng nhận tối đa (`maxReceiveCount`).
- **AWS Lambda (`order-processor`)**: Đọc tin nhắn theo batch, kiểm tra idempotency (xử lý lặp an toàn), ghi đơn hàng vào DynamoDB và trả về `batchItemFailures`.
- **Amazon DynamoDB (`Orders`)**: Lưu trữ thông tin đơn hàng với Partition Key `orderId`.
- **Amazon CloudWatch & SNS**: Giám sát tin nhắn trong DLQ qua CloudWatch Alarm và gửi cảnh báo email qua SNS Topic.

Chi tiết thiết kế và luồng lỗi xem tại [docs/architecture/README.md](docs/architecture/README.md).

## 2. Lộ Trình 4 Tuần (Roadmap)

- **Tuần 1**: Nghiên cứu kỹ thuật (Standard vs FIFO, DLQ); tài liệu kiến trúc & tạo sơ đồ kiến trúc chính thức; thiết lập truy cập AWS Learner Lab; thống nhất quy ước tag `Project`/`Owner`. *(Lưu ý: Sơ đồ kiến trúc và thiết lập môi trường là nhiệm vụ chính thức của tuần nhưng chưa thực thi trong gói tài liệu nền tảng này)*.
- **Tuần 2**: Cài đặt và kiểm thử đơn vị (Unit Test) các thành phần cốt lõi (`order-producer`, SQS/DLQ, `order-processor`, DynamoDB `Orders`).
- **Tuần 3**: Tích hợp hệ thống toàn diện, kiểm tra quyền `LabRole`, cấu hình CloudWatch Alarms -> SNS, tùy chọn cơ sở hạ tầng dưới dạng mã (IaC).
- **Tuần 4**: Kiểm thử tải (load script), kiểm thử đầu-cuối (E2E), tối ưu chi phí, dọn dẹp tài nguyên Lab, báo cáo tổng kết & video demo ($\le 10$ phút).

## 3. Phân Công Vai Trò (Ownership)

- **SV1: Quan (Leader)**: Phụ trách SQS, DLQ, Consumer `order-processor`, batch/concurrency, nghiên cứu Standard vs FIFO, tổng hợp kiến trúc và review nhóm.
- **SV2: Khôi**: Phụ trách API Gateway, Producer `order-producer`, DynamoDB `Orders`, SNS Topic, nghiên cứu retry/alerting, tích hợp README.
- **Phối hợp nhóm (Joint)**: Giám sát CloudWatch Alarms (điều phối chung, đầu mối chi tiết chờ chốt); thiết lập truy cập AWS Lab, quy ước tags, ghi nhận nhật ký worklog ($\ge 8$h/tuần/người), thu thập minh chứng và đồng giải trình dự án.

Chi tiết phân công xem tại [docs/task-assignment.md](docs/task-assignment.md).

## 4. Mục Lục Tài Liệu

- [docs/requirements.md](docs/requirements.md): Yêu cầu chức năng, phi chức năng và ràng buộc AWS Learner Lab.
- [docs/week1-plan.md](docs/week1-plan.md): Kế hoạch Tuần 1, phân định nhiệm vụ chính thức và các thử nghiệm tùy chọn.
- [docs/task-assignment.md](docs/task-assignment.md): Phân công trách nhiệm, ma trận phụ thuộc và cam kết thời gian.
- [docs/architecture/README.md](docs/architecture/README.md): Thiết kế kiến trúc, các luồng xử lý thất bại và checklist sơ đồ.
- [docs/research/standard-vs-fifo.md](docs/research/standard-vs-fifo.md): Nghiên cứu SQS Standard vs FIFO, cơ chế DLQ và kịch bản test.
- [docs/research/sv2-services.md](docs/research/sv2-services.md): Nghiên cứu dịch vụ SV2 (API Gateway, DynamoDB, SNS, Retry/Alerting).
- [docs/integration-contract.md](docs/integration-contract.md): Hợp đồng dữ liệu đề xuất, cơ chế idempotency và xử lý lỗi theo lô.
- [docs/aws-inventory.md](docs/aws-inventory.md): Danh mục tài nguyên AWS dự kiến (PLANNED) và ràng buộc tài khoản Lab.
- [docs/worklog/week1.md](docs/worklog/week1.md): Biểu mẫu nhật ký làm việc Tuần 1 (mẫu trống chờ ghi nhận giờ thực tế).
- [docs/evidence/week1/README.md](docs/evidence/week1/README.md): Hướng dẫn minh chứng và quy tắc che giấu thông tin nhạy cảm.
- [docs/ai-usage.md](docs/ai-usage.md): Minh bạch việc sử dụng AI hỗ trợ phác thảo tài liệu nền tảng.
