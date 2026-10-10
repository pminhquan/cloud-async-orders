# Báo Cáo Minh Bạch Về Sử Dụng Trí Tuệ Nhân Tạo (AI Usage Statement)

Tài liệu công khai phạm vi sử dụng công cụ Trí tuệ Nhân tạo (AI), ghi nhận thực tế đã xác minh, và cung cấp biểu mẫu khai báo chi tiết hàng tuần cho dự án **cloud-async-orders**.

## 1. Tóm Tắt Sử Dụng AI Thực Tế Đã Xác Minh (Verified Actual Usage)

- **Codex**: Điều phối quy trình (orchestration) và kiểm tra xác thực định dạng tĩnh (static validation). Phiên bản/Model chính xác: **Chưa xác minh** (không suy diễn từ nhãn công cụ). Lịch sử prompt/output gốc: **Chưa bổ sung / chưa xác minh**.
- **Antigravity Desktop**: Soạn thảo và cập nhật các tài liệu nền tảng qua các job bridge 001-003 và follow-up 004. Phiên bản/Model chính xác: **Chưa xác minh** (không suy diễn từ thương hiệu hay hệ thống). Lịch sử prompt/output gốc: **Chưa bổ sung / chưa xác minh**.
- **ChatGPT**: **Chưa được xác nhận** trong bằng chứng thực tế của dự án; được hỗ trợ khai báo nếu sinh viên có sử dụng thực tế trong quá trình làm bài.
- **Rà soát con người**: Toàn bộ nội dung hiện ở trạng thái **CHỜ SINH VIÊN RÀ SOÁT (PENDING)**. Việc hoàn thành gói tài liệu nền tảng (**docs-only job**) **KHÔNG đồng nghĩa với việc Tuần 1 đã hoàn thành**.

## 2. Biểu Mẫu Khai Báo Chi Tiết Hàng Tuần (Weekly AI Interaction Log Template)

Biểu mẫu trống chuẩn hóa phục vụ việc khai báo từng lần tương tác AI của sinh viên trong suốt 4 tuần:

| Trường thông tin | Giá trị mẫu / Hướng dẫn điền |
| :--- | :--- |
| **Tuần (Week)** | *[Điền: Tuần 1, 2, 3, hoặc 4]* |
| **Sinh viên (Student)** | *[Quan hoặc Khôi]* |
| **Nhiệm vụ (Task)** | *[Mã nhiệm vụ liên quan, ví dụ W1-T01]* |
| **Công cụ AI (AI Tool)** | *[Codex / Antigravity / ChatGPT / Khác]* |
| **Model / Phiên bản chính xác** | *[Phiên bản chính xác hoặc ghi "Chưa xác minh"]* |
| **Nguồn xác minh (Source Verification)** | *[UI / Chat export / API log]* |
| **Prompt gốc (Original Prompt)** | *[Nguyên văn prompt hoặc tham chiếu artifact; che secret nếu có]* |
| **Kết quả AI tạo ra (AI Output)** | *[Nguyên văn kết quả AI tạo hoặc tham chiếu artifact]* |
| **Bản sinh viên đã sửa (Reviewed Version)** | *[Nội dung thực tế sau khi sinh viên chỉnh sửa, kiểm tra]* |
| **Nội dung thay đổi & Lý do** | *[Giải trình cụ thể các điểm sửa chữa và lý do kỹ thuật]* |
| **Trạng thái rà soát (Review Status)** | *[Pending / Reviewed & Approved / Rejected]* |

*(Bản gốc chứa dữ liệu nhạy cảm nếu có phải giữ riêng tư ngoài repo; bản công khai trên GitHub phải được lọc bỏ hoàn toàn secrets).*

## 3. Các Quyết Định Kỹ Thuật Còn Tồn Đọng (Unresolved Decisions)

1. **Lựa chọn SQS Standard hay FIFO**: Chốt phương án dựa trên phân tích tại [docs/research/standard-vs-fifo.md](research/standard-vs-fifo.md).
2. **Phương án tài khoản Lab**: Kiểm tra Console thực tế để quyết định triển khai 1 tài khoản chính hay 2 tài khoản theo [docs/aws-inventory.md](aws-inventory.md).
3. **Phân công CloudWatch Alarm**: Xác định thành viên phụ trách cụ thể trong nhóm theo [docs/task-assignment.md](task-assignment.md).
4. **Quy ước tag chính thức**: Chốt giá trị tag `Project` và `Owner` cho các tài nguyên.
