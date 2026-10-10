# Danh Mục Tài Nguyên AWS Dự Kiến (AWS Resource Inventory)

Tài liệu liệt kê các tài nguyên đám mây dự kiến được sử dụng trong dự án **cloud-async-orders**, cùng các ràng buộc về môi trường AWS Learner Lab.

> [!IMPORTANT]
> **TẤT CẢ CÁC HÀNG TRONG DANH MỤC DƯỚI ĐÂY Ở TRẠNG THÁI LÊN KẾ HOẠCH (PLANNED).**
> - **Phân loại trạng thái**: **PLANNED** (thiết kế dự kiến); **VERIFIED** (đã kiểm tra đối soát với Console thực tế và có minh chứng); **CREATED** (tài nguyên thực tế đã tạo trên AWS và có minh chứng). Hiện tại **chưa có hàng nào chuyển sang VERIFIED hoặc CREATED**; chưa có tài nguyên nào được tạo trên AWS.

## 1. Bảng Danh Mục Tài Nguyên Dự Kiến (Planned Resources)

| Tên tài nguyên đề xuất | Dịch vụ AWS | Mục đích kỹ thuật | Đầu mối phụ trách | Trạng thái | Tag đề xuất | Ghi chú & Ràng buộc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `api-async-orders` | Amazon API Gateway | Nhận `POST /orders` từ client | Khôi (SV2) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: khoi-sv2` | REST hoặc HTTP API |
| `order-producer` | AWS Lambda | Validate và gửi tin nhắn SQS | Khôi (SV2) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: khoi-sv2` | Gán IAM `LabRole` có sẵn |
| `orders-queue` | Amazon SQS | Hàng đợi đệm đơn hàng | Quan (SV1) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: quan-sv1` | Standard hoặc FIFO; gắn kèm DLQ |
| `orders-dlq` | Amazon SQS | Dead Letter Queue cô lập lỗi | Quan (SV1) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: quan-sv1` | Cùng loại hàng đợi với queue nguồn |
| `order-processor` | AWS Lambda | Xử lý tin nhắn và ghi DynamoDB | Quan (SV1) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: quan-sv1` | Kích hoạt bởi SQS ESM, gán `LabRole` |
| `Orders` | Amazon DynamoDB | Lưu trữ đơn hàng | Khôi (SV2) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: khoi-sv2` | Partition Key `orderId` |
| `dlq-alarm-messages-visible` | Amazon CloudWatch | Giám sát số tin nhắn trong DLQ | Phối hợp nhóm (Joint) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: team-joint` | Đầu mối phụ trách chi tiết chờ chốt |
| `order-processing-alerts` | Amazon SNS | Gửi cảnh báo lỗi qua email | Khôi (SV2) | **PLANNED** | `Project: cloud-async-orders`<br>`Owner: khoi-sv2` | Giao thức Email |

## 2. Ràng Buộc Nền Tảng AWS Learner Lab

- **Vùng triển khai (Proposed Region)**: Đề xuất `us-east-1` hoặc `us-west-2` (PROPOSED, chờ xác nhận trong Lab Console). Tất cả tài nguyên phải nằm trên cùng một Region.
- **Vai trò thực thi (IAM Role)**: Bắt buộc: **Không tạo IAM users hoặc IAM roles mới; chỉ dùng vai trò/profile được Lab cho phép**. Các hàm Lambda sử dụng vai trò thực thi `LabRole` có sẵn; `LabInstanceProfile` là EC2 instance profile có sẵn, không phải role của Lambda (dự án không dùng và không lên kế hoạch tạo EC2/EBS). Quyền hạn cụ thể của `LabRole` ở trạng thái CHƯA RÕ (UNKNOWN) cho đến khi kiểm tra thực tế trong Console; không tự ý khẳng định các chính sách IAM là không thể chỉnh sửa hoặc tài khoản được cấp quyền chia sẻ.
- **Quy ước Gán Thẻ (Tags)**: Bắt buộc 2 tag key: `Project` và `Owner`. Các giá trị cụ thể ở bảng trên ở trạng thái đề xuất (PROPOSED) chờ hai sinh viên thống nhất.
- **Ràng buộc hai tài khoản Learner Lab**: Hai sinh viên có thể sở hữu hai tài khoản Lab riêng biệt. Nếu khác tài khoản, việc tích hợp API/Lambda/SQS/DynamoDB bắt buộc phải có quyền và chính sách tài nguyên chéo (cross-account permissions/policies) được kiểm chứng, không được mặc định cho phép. Đề xuất triển khai trên cùng một tài khoản chính (PROPOSED) tùy quy định môn học. Tuyệt đối không chia sẻ thông tin đăng nhập và không công khai Account ID.
