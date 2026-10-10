# Phân Công Nhiệm Vụ & Ma Trận Phụ Thuộc (Task Assignment)

Tài liệu xác định vai trò, trách nhiệm, ma trận phụ thuộc và phân bổ công việc theo 4 tuần cho từng thành viên trong nhóm **cloud-async-orders**.

## 1. Ràng Buộc Thời Gian Làm Việc

- Mỗi sinh viên bắt buộc hoàn thành và ghi nhận tối thiểu **8 giờ làm việc thực tế mỗi tuần** (`>= 8 ACTUAL documented hours/week`), đạt tổng tối thiểu 32 giờ thực tế/người trong 4 tuần.
- Kế hoạch công việc không được tính vào giờ thực tế. Mọi giờ làm việc phải được ghi nhận trung thực tại [docs/worklog/week1.md](worklog/week1.md) và đối soát với minh chứng tại [docs/evidence/week1/README.md](evidence/week1/README.md).

## 2. Phân Công Trách Nhiệm (Ownership)

- **SV1: Quan (Trưởng nhóm / Leader)**:
  - Phụ trách chính: Amazon SQS (Standard/FIFO), Dead Letter Queue (DLQ), Consumer Lambda `order-processor`, cấu hình Batch Size & Concurrency, nghiên cứu kỹ thuật hàng đợi ([docs/research/standard-vs-fifo.md](research/standard-vs-fifo.md)), tổng hợp kiến trúc tổng thể và rà soát chất lượng kỹ thuật toàn nhóm.
- **SV2: Khôi (Thành viên)**:
  - Phụ trách chính: Amazon API Gateway, Producer Lambda `order-producer`, Amazon DynamoDB `Orders`, Amazon SNS Topic, nghiên cứu kỹ thuật dịch vụ và cơ chế retry/alerting ([docs/research/sv2-services.md](research/sv2-services.md)), quản lý hợp đồng dữ liệu và tích hợp [README.md](../README.md).
- **Phối hợp nhóm (Joint)**:
  - Amazon CloudWatch Alarms: Điều phối chung giữa hai thành viên, đầu mối phụ trách chi tiết sẽ chốt trong quá trình triển khai.
  - Cả hai thành viên cùng thực hiện: Thiết lập môi trường AWS Learner Lab, xác minh `LabRole`, tuân thủ quy ước tag `Project`/`Owner`, ghi chép worklog, thu thập minh chứng và đồng giải trình hệ thống trong buổi demo.

## 3. Ma Trận Phụ Thuộc Giữa Các Tác Vụ (Task Dependencies)

```
[Hợp đồng tích hợp (Contract)] ──┬──► [Producer Lambda: order-producer] ──► [Amazon SQS Queue]
                                 │                                                 │
                                 └──► [Consumer Lambda: order-processor] ◄────────┘
                                             │                                     │
                                             ▼ (PutItem)                           ▼ (Sau maxReceiveCount)
                                  [DynamoDB Table: Orders]                 [Amazon SQS DLQ]
                                                                                   │
                                                                                   ▼
                                                                        [CloudWatch Alarm & SNS]
```

- `integration-contract.md` là điều kiện tiên quyết cho việc phát triển `order-producer`, `order-processor` và thiết kế bảng DynamoDB.
- SQS Queue và DynamoDB `Orders` là điều kiện tiên quyết để hoàn thiện và kiểm thử Consumer Lambda.
- SQS DLQ là điều kiện tiên quyết để cấu hình CloudWatch Alarm và kiểm thử thông báo qua SNS Topic.
- Toàn bộ các dịch vụ tích hợp hoàn chỉnh là điều kiện tiên quyết cho việc kiểm thử tải và kiểm thử đầu-cuối (E2E) trong Tuần 4.

## 4. Tóm Tắt Lộ Trình Phân Bổ 4 Tuần

- **Tuần 1**: Nghiên cứu kỹ thuật, lập tài liệu nền tảng, thiết kế kiến trúc & tạo sơ đồ kiến trúc chính thức, kiểm tra truy cập Lab và xác định quy ước tags.
- **Tuần 2**: Cài đặt mã nguồn và kiểm thử đơn vị (Unit Test) cho các thành phần độc lập (`order-producer`, SQS/DLQ, `order-processor`, DynamoDB).
- **Tuần 3**: Tích hợp luồng hoàn chỉnh API -> SQS -> Lambda -> DynamoDB, thiết lập DLQ, cấu hình CloudWatch Alarm và SNS, tùy chọn IaC.
- **Tuần 4**: Viết script kiểm thử tải, đo đạc độ trễ/thông lượng, kiểm tra kịch bản lỗi, tối ưu chi phí, hoàn thiện báo cáo và quay video demo ($\le 10$ phút).
