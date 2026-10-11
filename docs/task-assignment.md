# Phân công nhiệm vụ

## 1. Trách nhiệm

| Thành viên | Phạm vi phụ trách |
| :--- | :--- |
| **Quan — SV1, trưởng nhóm** | Nghiên cứu Standard/FIFO; cấu hình SQS/DLQ, Consumer `order-processor`, trigger/batch/concurrency; test valid/invalid/retry/DLQ; minh chứng và tài liệu kỹ thuật SV1; sơ đồ kiến trúc tổng thể; rà soát kỹ thuật và phối hợp tích hợp Consumer ở giai đoạn sau. |
| **Khôi — SV2** | API Gateway/Producer, DynamoDB, SNS/CloudWatch và thông báo lỗi; nghiên cứu retry/DLQ/alerting; minh chứng SV2, phối hợp hợp đồng dữ liệu; tổng hợp README/GitHub, báo cáo tuần và khai báo AI riêng. |

Quan cung cấp cấu hình DLQ, kết quả Consumer và thông tin trung thực về phần việc/AI của mình cho Khôi tổng hợp. Quan không phải duy trì bản báo cáo trùng; không ai được bịa, bỏ sót đóng góp hoặc phê duyệt thay người khác.

Cả hai phối hợp kiểm tra Lab, quyền `LabRole`, Region/tài khoản, tags, minh chứng và giải trình hệ thống khi demo. PoC SV1 dùng **batch size 1**, **maximum concurrency 2**; ví dụ 5/5 không phải cấu hình triển khai.

## 2. Giờ làm và minh chứng

Mỗi sinh viên phải ghi ít nhất **8 giờ thực tế/tuần**, tổng tối thiểu 32 giờ/người trong 4 tuần. Kế hoạch và thời gian chạy AI không thay thế giờ làm. Quan bổ sung thời gian vào [nhật ký Tuần 1](worklog/week1.md), đối chiếu [minh chứng](evidence/week1/README.md); Khôi tổng hợp báo cáo riêng từ thông tin từng người xác nhận.

## 3. Phối hợp kỹ thuật

- [Hợp đồng tích hợp](integration-contract.md) thống nhất schema cho Producer, Consumer và DynamoDB. SQS và bảng Orders là điều kiện để hoàn thiện Consumer có lưu trữ.
- Quan phụ trách [sơ đồ kiến trúc](architecture/README.md); Khôi cung cấp và xác nhận phần SV2. Khung SV1/SV2 thể hiện trách nhiệm, không mặc định cùng hoặc khác tài khoản AWS.
- DLQ và kết quả lỗi/retry là đầu vào để Khôi cấu hình CloudWatch/SNS. Kiểm thử E2E/tải cần các thành phần đã tích hợp.

Lộ trình chung xem [README](../README.md); nhiệm vụ hiện tại theo [kế hoạch Tuần 1](week1-plan.md).
