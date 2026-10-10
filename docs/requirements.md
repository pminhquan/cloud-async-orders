# Yêu Cầu Dự Án & Ràng Buộc Kỹ Thuật (Requirements)

Tài liệu xác định các yêu cầu chức năng, phi chức năng, ràng buộc môi trường và kết quả bàn giao cho dự án **cloud-async-orders**.

## 1. Yêu Cầu Chức Năng (Functional Requirements)

- **Tiếp nhận đơn hàng (API Ingestion)**: Amazon API Gateway cung cấp endpoint `POST /orders`. Producer Lambda (`order-producer`) validate dữ liệu đầu vào cơ bản và gửi tin nhắn vào SQS. Trả về mã phản hồi `202 Accepted` chỉ khi gửi SQS thành công; trả về `400 Bad Request` nếu payload sai định dạng, `5xx` nếu gửi SQS thất bại.
- **Hàng đợi thông điệp (Message Queue)**: Amazon SQS đóng vai trò vùng đệm phân tách tiếp nhận và xử lý. Nghiên cứu phương án Standard Queue vs FIFO Queue. Cấu hình Dead Letter Queue (DLQ) để cách ly tin nhắn lỗi sau ngưỡng nhận tối đa (`maxReceiveCount`).
- **Xử lý đơn hàng & Idempotency**: Consumer Lambda (`order-processor`) nhận tin nhắn theo batch, kiểm tra idempotency (xử lý lặp an toàn) dựa trên khóa `orderId`, thực hiện conditional write vào DynamoDB `Orders`, và báo cáo `batchItemFailures`.
- **Lưu trữ trạng thái (Persistence)**: Amazon DynamoDB lưu thông tin đơn hàng với Partition Key `orderId`.
- **Giám sát & Cảnh báo (Monitoring & Alerting)**: CloudWatch Alarm theo dõi tin nhắn trong DLQ, kích hoạt thông báo email qua Amazon SNS Topic khi có sự cố.
- **Kịch bản kiểm thử (Testing)**: Xây dựng kịch bản kiểm thử tải (load script) và kịch bản kiểm thử lỗi/retry/DLQ.

## 2. Ràng Buộc Phi Chức Năng & AWS Learner Lab

- **Nhân sự & Thời gian**: 2 sinh viên trong 4 tuần. Mỗi sinh viên bắt buộc hoàn thành và ghi nhận tối thiểu **8 giờ thực tế mỗi tuần** (`>= 8 ACTUAL documented hours/week`). Kế hoạch công việc không tính là giờ thực tế; đối soát tại [docs/worklog/week1.md](worklog/week1.md).
- **Quyền hạn IAM**: Bắt buộc: **Không tạo IAM users hoặc IAM roles mới; chỉ dùng vai trò/profile được Lab cho phép**. Lambda sử dụng vai trò thực thi `LabRole` có sẵn; `LabInstanceProfile` là EC2 instance profile có sẵn, không phải role của Lambda (dự án không dùng và không lên kế hoạch tạo EC2/EBS). Quyền hạn cụ thể của `LabRole` ở trạng thái CHƯA RÕ (UNKNOWN) cho đến khi kiểm tra trực tiếp trong Console.
- **Giới hạn Concurrency**: Toàn bộ tài khoản Lab bị giới hạn tối đa **10 concurrent Lambda executions** (tính chung cho producer, consumer và các hàm khác). Tránh tạo các tài nguyên tốn kém không cần thiết như EC2 hoặc EBS.
- **Quy ước Gán nhãn (Tagging)**: Mọi tài nguyên bắt buộc có 2 tag key: `Project` và `Owner` (giá trị cụ thể ở trạng thái PROPOSED chờ nhóm thống nhất).
- **Vùng triển khai (Region)**: Đề xuất `us-east-1` hoặc `us-west-2` (PROPOSED, chờ xác nhận trong Lab).
- **Ràng buộc hai tài khoản Learner Lab**: Hai sinh viên có thể sở hữu hai tài khoản Lab riêng biệt. Nếu khác tài khoản, việc tích hợp API/Lambda/SQS/DynamoDB bắt buộc phải có quyền và chính sách tài nguyên chéo (cross-account permissions/policies) được kiểm chứng, không được mặc định cho phép. Đề xuất triển khai trên cùng một tài khoản chính (PROPOSED) tùy quy định môn học. Tuyệt đối không chia sẻ thông tin đăng nhập và không công khai Account ID.

## 3. Danh Mục Kết Quả Bàn Giao (Deliverables)

- Mã nguồn và cấu hình công khai trên GitHub repository.
- Bộ tài liệu kỹ thuật đầy đủ trong thư mục `docs/`.
- Nhật ký làm việc định kỳ ([docs/worklog/](worklog/week1.md)), minh chứng bản sao che chắn & bản gốc riêng tư ([docs/evidence/](evidence/week1/README.md)), và biểu mẫu khai báo AI ([docs/ai-usage.md](ai-usage.md)).
- **Báo cáo chi phí cuối kỳ (Final Cost Report - Tuần 4)**: Nêu rõ nguồn tính chi phí, chu kỳ sử dụng thực tế, bóc tách theo từng dịch vụ AWS; phân biệt rạch ròi giữa ước tính lý thuyết và số liệu thực tế; giải trình các hạn chế nếu không truy cập được Billing Console trên Lab; tuyệt đối không bịa đặt số liệu chi phí.
- Báo cáo tổng kết dự án và video demo thời lượng $\le 10$ phút; cả hai sinh viên nắm rõ và giải trình được toàn bộ hệ thống.
