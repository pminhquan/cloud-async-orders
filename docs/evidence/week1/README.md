# Thư Mục Minh Chứng Tuần 1 (Week 1 Evidence Archive)

Tài liệu quy định quản lý minh chứng, bảo vệ thông tin định danh và theo dõi đối soát thực tế cho Tuần 1 của dự án **cloud-async-orders**.

## 1. Quy Định Quản Lý Minh Chứng: Bản Gốc Riêng Tư vs Bản Sao Công Khai

- **Bản gốc riêng tư (Private Originals - Nộp riêng giảng viên)**:
  - Giảng viên yêu cầu ảnh chụp màn hình gốc hiển thị rõ: **AWS Account ID thực tế**, **Region thực tế** và **thời gian chụp thực tế** kèm múi giờ đồng hồ rõ ràng trên màn hình Console.
  - Lưu trữ: Bản gốc được lưu trữ **hoàn toàn bên ngoài repo công khai và lịch sử Git**, chỉ gửi qua kênh nộp bài riêng tư được giảng viên phê duyệt (không cần tạo thư mục riêng trong repo lúc này).
  - An toàn thông tin: Bản gốc cũng **tuyệt đối không được chứa** thông tin xác thực nhạy cảm (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, mật khẩu, cookie phiên). Sinh viên cần tránh chụp các màn hình nhạy cảm này hoặc chụp lại an toàn; không lưu giữ bất kỳ bản gốc nào mang credential.
  - Liêm chính: Tuyệt đối không chỉnh sửa Account ID, Region hay thời gian trên ảnh gốc để đối phó tiêu chí; giữ nguyên đồng hồ và múi giờ thực tế.
- **Bản sao công khai (Public Redacted Copies - Đưa lên GitHub)**:
  - Chỉ đưa vào thư mục này các bản sao đã **che mờ/bôi đen vĩnh viễn** Account ID và thông tin định danh cá nhân riêng tư.
  - Giữ lại Region không nhạy cảm và timestamp/timezone thực tế để hỗ trợ đối soát minh bạch. Tuyệt đối không tạo ảnh mô phỏng hay timestamp giả mạo.

## 2. Biểu Mẫu Theo Dõi Minh Chứng Đối Soát (Tracking Template)

Biểu mẫu trống phục vụ đối soát giữa bản nộp riêng tư cho giảng viên và bản sao lưu trữ công khai:

| Mã Ref | Thời gian chụp (UTC/Local) | Region | Sinh viên | Nội dung kiểm tra | Tham chiếu nộp riêng tư | Tham chiếu bản sao công khai |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| REF-01 | *[Chờ ghi nhận]* | *[Chờ]* | *[Chờ]* | Xác minh Console active & Region | *[Kênh nộp riêng]* | `docs/evidence/week1/...` |
| REF-02 | *[Chờ ghi nhận]* | *[Chờ]* | *[Chờ]* | Xác minh tồn tại IAM LabRole | *[Kênh nộp riêng]* | `docs/evidence/week1/...` |
| REF-03 | *[Chờ ghi nhận]* | *[Chờ]* | *[Chờ]* | Xác thực tag Project/Owner | *[Kênh nộp riêng]* | `docs/evidence/week1/...` |

## 3. Danh Mục Kiểm Tra Minh Chứng Dự Kiến (Planned Checklist)

Bảng checklist dưới đây ở trạng thái kế hoạch (**CHƯA CÓ MINH CHỨNG NÀO ĐƯỢC TẠO**):

| STT | Hạng mục minh chứng | Mô tả chi tiết | Tên file bản sao công khai dự kiến | Trạng thái |
| :---: | :--- | :--- | :--- | :---: |
| 1 | Xác minh quyền truy cập AWS Console | Ảnh chụp console hoạt động, đã che Account ID | `docs/evidence/week1/aws-console-active.png` | [ ] Chưa có |
| 2 | Xác minh tồn tại IAM `LabRole` | Ảnh chụp IAM Console hiển thị `LabRole` | `docs/evidence/week1/iam-labrole-check.png` | [ ] Chưa có |
| 3 | Xác nhận Vùng triển khai (Chosen Region) | Ảnh chụp/ghi chú xác nhận Region (`us-east-1`/`us-west-2`) | `docs/evidence/week1/aws-region-confirmed.png` | [ ] Chưa có |
| 4 | Kết luận an toàn về tương thích tài khoản | Ghi chú an toàn chung/riêng tài khoản (không lộ ID) | `docs/evidence/week1/account-compatibility.md` | [ ] Chưa có |
| 5 | Sơ đồ kiến trúc chính thức Tuần 1 | File sơ đồ hoàn chỉnh theo yêu cầu Tuần 1 | `docs/evidence/week1/architecture-diagram.png` | [ ] Chưa có |
| 6 | Biên bản họp nhóm thống nhất Tuần 1 | Ghi chú cuộc họp thảo luận kiến trúc và phân công | `docs/evidence/week1/meeting-notes-week1.md` | [ ] Chưa có |
| 7 | Xác thực tag Project/Owner thực tế | Minh chứng kiểm tra tag khi tài nguyên được phép tạo | `docs/evidence/week1/resource-tags-verified.txt` | [ ] Chưa có |
| 8 | Working-tree diff / log tài liệu | Minh chứng tiến độ tài liệu nền tảng nhánh `docs/week1-foundation` | `docs/evidence/week1/git-diff-week1.txt` | [ ] Chưa có |

Khi cập nhật minh chứng, sinh viên đối soát với biểu mẫu trên và liên kết vào [docs/worklog/week1.md](../../worklog/week1.md).
