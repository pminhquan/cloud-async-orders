# Hướng dẫn đóng góp

Áp dụng cho mọi thay đổi mới từ Tuần 4 trở đi. Lịch sử commit/nhánh cũ được giữ nguyên để bảo toàn truy vết.

## 1. Nhánh

Dùng `<type>/<scope>-<mô-tả>`, chữ thường, nối bằng dấu gạch nối:

- `feat/` — chức năng mới
- `fix/` — sửa lỗi
- `docs/` — tài liệu
- `test/` — kiểm thử
- `refactor/` — tái cấu trúc
- `chore/` — cấu hình, công cụ

Ví dụ: `docs/repository-cleanup-week4-audit`, `fix/producer-validation`. Không dùng tên cá nhân, tên công cụ AI hoặc ngày tháng không cần thiết.

## 2. Commit

Theo Conventional Commits: `type(scope): mô tả ngắn`.

Ví dụ: `docs(week4): chuẩn hóa README và liên kết minh chứng`.

Mỗi commit nên tập trung một nhóm thay đổi; không sửa file ngoài phạm vi PR.

## 3. Pull Request

- Tiêu đề ngắn, đúng phạm vi, ưu tiên tiếng Việt.
- Mô tả gồm: mục tiêu, thay đổi chính, cách kiểm tra, ảnh hưởng tài liệu/minh chứng và giới hạn.
- Không merge trực tiếp vào `main`; mọi thay đổi đi qua PR và review.
- Không force-push `main`, không rebase/amend commit đã công bố, không đổi tác giả.
- Không xóa nhánh đang gắn PR mở hoặc worktree đang dùng.

## 4. Minh chứng

- Đặt ảnh/dữ liệu trong `docs/evidence/weekN/`, giữ tên mô tả và đúng thư mục tuần.
- Ghi rõ ngày, môi trường (Lab nào), `runId`/`orderId` và phạm vi phép thử.
- Phân biệt kiểm thử offline/mô phỏng với kết quả AWS thật; không suy diễn `202` thành `PROCESSED`.
- Không chụp hoặc commit credential, token, email cá nhân, Account ID chưa che.

## 5. Bảo mật

Không commit access key, secret key, session token, password, file credentials hoặc thông tin đăng nhập Learner Lab. Trước khi push, rà soát diff và ảnh minh chứng.

## 6. Kiểm tra trước khi mở PR

```bash
python -m pytest -q
python -B -m unittest discover -s tests -p "test_*.py"
python -m compileall -q src scripts tests
cfn-lint iac/week3-monitoring.yaml
git diff --check
```

Kiểm tra liên kết Markdown, đường dẫn ảnh và không còn tham chiếu tới file đã di chuyển/xóa. Ghi kết quả CI theo đúng head commit của PR.
