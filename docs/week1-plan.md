# Kế Hoạch Chi Tiết Tuần 1 (Week 1 Action Plan)

Tài liệu xác định các mục tiêu, nhiệm vụ chính thức và tiêu chuẩn bàn giao cho Tuần 1 của dự án **cloud-async-orders**.

## 1. Mục Tiêu Tuần 1 (Week 1 Objectives)

- Thiết lập tài liệu nền tảng, kiến trúc hệ thống và hợp đồng tích hợp dữ liệu.
- Hoàn thành nghiên cứu kỹ thuật các dịch vụ AWS: SQS Standard vs FIFO & DLQ (SV1 Quan) và API Gateway, DynamoDB, SNS, Retry/Alerting (SV2 Khôi).
- Hoàn thành các nhiệm vụ nền tảng bắt buộc của Tuần 1: Tạo sơ đồ kiến trúc chính thức (Architecture Diagram Deliverable), thiết lập truy cập AWS Learner Lab, kiểm tra quyền `LabRole`, xác định Region/tương thích tài khoản, và thiết lập quy ước tag `Project`/`Owner`.
- Thiết lập khung nhật ký làm việc (worklog $\ge 8$h/tuần/người) và checklist minh chứng bảo mật.

## 2. Bảng Nhiệm Vụ Chính Thức Tuần 1 (Official Week 1 Tasks)

| Mã CV | Tên công việc | Người phụ trách | Điều kiện tiên quyết | Kết quả bàn giao | Tiêu chí nghiệm thu | Minh chứng liên kết |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **W1-T01** | Xây dựng bộ tài liệu kỹ thuật nền tảng | Khôi & Quan | Repo Git khởi tạo | README.md và các file docs theo danh mục | Đầy đủ nội dung, liên kết hợp lệ, không lỗi cú pháp | Working-tree diff |
| **W1-T02a** | Nghiên cứu kỹ thuật SQS Standard vs FIFO & DLQ | Quan (Leader) | Tài liệu AWS chính thức | [docs/research/standard-vs-fifo.md](research/standard-vs-fifo.md) | So sánh định tính, trích dẫn chuẩn xác, kịch bản test dự kiến | Nội dung tài liệu |
| **W1-T02b** | Nghiên cứu dịch vụ SV2 (API GW, DynamoDB, SNS, Alert) | Khôi | Tài liệu AWS chính thức | [docs/research/sv2-services.md](research/sv2-services.md) | Phân tích kỹ thuật các dịch vụ phụ trách, tổng hợp câu hỏi tồn đọng | Nội dung tài liệu |
| **W1-T03** | Tạo sơ đồ kiến trúc chính thức (Diagram Deliverable) | Quan & Khôi | Thiết kế kiến trúc sơ bộ | File sơ đồ kiến trúc hoàn chỉnh | Thể hiện đủ các thành phần theo checklist, luồng chính và luồng lỗi | File sơ đồ trong repo *(Chưa thực thi)* |
| **W1-T04** | Thiết lập môi trường Lab & kiểm tra quyền truy cập | Quan & Khôi | Cấp tài khoản Lab | Báo cáo kiểm tra truy cập | Xác định Region khả dụng, quyền `LabRole`, đối soát tương thích tài khoản | Checklist evidence *(Chưa thực thi)* |
| **W1-T05** | Thiết lập quy ước tag & kế hoạch xác thực tag | Khôi & Quan | Yêu cầu môn học | Bảng quy ước tag trong inventory | Quy ước key/value đề xuất; nghiệm thu tag Project/Owner thực tế khi tạo tài nguyên | Inventory; bằng chứng gắn tag khi tài nguyên được tạo *(Chưa thực thi)* |
| **W1-T06** | Khung nhật ký làm việc ($\ge 8$h) & Minh chứng | Khôi & Quan | Quy định giờ làm việc | Template worklog & evidence | Biểu mẫu trống sẵn sàng, quy tắc che giấu secret | [docs/worklog/week1.md](worklog/week1.md) |
| **W1-T07** | Báo cáo minh bạch sử dụng AI | Khôi & Quan | Quy chế học thuật | [docs/ai-usage.md](ai-usage.md) | Ghi nhận trung thực, trạng thái chờ sinh viên duyệt | Nội dung tài liệu |

> [!IMPORTANT]
> **PHÂN ĐỊNH TRÁCH NHIỆM THỰC THI**:
> - Các nhiệm vụ nền tảng gồm **W1-T03** (tạo sơ đồ kiến trúc), **W1-T04** (thiết lập/kiểm tra truy cập Lab) và kiểm tra tag thực tế của **W1-T05** là nhiệm vụ bắt buộc của Tuần 1, nhưng ở trạng thái **KẾ HOẠCH (PLANNED / CHƯA THỰC THI)** cho đến khi có bằng chứng thực tế từ hai sinh viên. Gói công việc tài liệu hiện tại (**docs-only job**) tuyệt đối không thực hiện thao tác đám mây nào và không tạo sơ đồ giả mạo.
> - Quy tắc gán tag được áp dụng và xác minh trên bất kỳ tài nguyên nào được cấp phép tạo thực tế; không yêu cầu tạo tài nguyên rác không sử dụng chỉ để chụp ảnh màn hình.
> - Ràng buộc cứng: Không tạo IAM user/role mới; chỉ dùng `LabRole`/`LabInstanceProfile` có sẵn; tổng concurrency $\le 10$; cam kết tối thiểu 8 giờ thực tế/tuần mỗi sinh viên.

## 3. Hoạt Động Tuần 2 & Các Thử Nghiệm Tùy Chọn (Prototypes)

- **Tuần 2 chính thức**: Triển khai và kiểm thử đơn vị hoàn chỉnh các thành phần cốt lõi (`order-producer`, hàng đợi SQS, `order-processor`, DynamoDB `Orders`).
- **Thử nghiệm prototype sớm (Optional Early Prototypes)**: Các thử nghiệm sớm về mã nguồn SQS/Lambda chỉ được tiến hành khi có sự cho phép của môn học/giảng viên, hoàn toàn tùy chọn và nằm ngoài gói công việc tài liệu nền tảng hiện tại.
