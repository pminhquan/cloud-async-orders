# Hướng dẫn đóng góp

Mỗi Pull Request tập trung vào một phạm vi có thể kiểm tra, giữ nguyên hành vi ngoài phạm vi và dẫn chiếu kết quả xác minh phù hợp.

## 1. Tên nhánh

Dùng mẫu `<type>/<scope>-<description>`, viết thường và phân tách bằng dấu gạch nối. Các loại thường dùng: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

Ví dụ: `docs/week4-finalization`, `fix/producer-validation`, `test/consumer-idempotency`. Không đưa tên cá nhân, tên công cụ tự động, mã thực thi hoặc ngày tháng không cần thiết vào tên nhánh mới.

## 2. Commit và Pull Request

Commit tuân theo Conventional Commits: `type(scope): description`.

Ví dụ: `docs(week4): finalize acceptance report and technical documentation`.

Tiêu đề PR phản ánh đúng phạm vi; phần mô tả viết bằng tiếng Việt, nêu mục tiêu, thay đổi, kiểm thử, tài liệu/minh chứng và giới hạn liên quan. Ví dụ: `docs(week4): hoàn thiện nghiệm thu và báo cáo cuối kỳ`.

Giữ đúng danh tính tác giả Git. Quy ước tên trung tính không thay đổi quyền tác giả hoặc việc khai báo công cụ hỗ trợ theo [tài liệu AI](docs/ai-declaration.md).

## 3. Kiểm tra và bảo vệ lịch sử

- Đọc toàn bộ diff và chỉ stage các đường dẫn thuộc phạm vi PR.
- Kiểm tra test phù hợp, liên kết tài liệu, whitespace và thông tin nhạy cảm.
- Phân biệt kiểm thử mô phỏng với nghiệm thu trên AWS; gắn kết quả CI với đúng head commit.
- Không đưa credential, session token hoặc cấu hình phục hồi riêng vào PR. Minh chứng học phần giữ MSSV và thông tin sinh viên theo yêu cầu của môn học.
- Không đổi tên/xóa nhánh đang gắn với worktree hoặc PR để làm đẹp lịch sử; không sửa commit đã công bố bằng force-push chỉ vì quy ước tên.
- Chỉ hợp nhất vào `main` sau bước review và phê duyệt tương ứng.
