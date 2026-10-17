# Hướng dẫn chốt repository để nộp

## 1. Không push các file không cần thiết

Không push:

```text
.git/
backup/
AWS credentials
file tạm cá nhân
ảnh ngoài project
```

## 2. Kiểm tra source

```bash
python -m pytest -q
```

Kết quả hiện tại của bộ source này:

```text
33 passed, 81 subtests passed
```

## 3. Kiểm tra tài liệu

Bắt buộc đọc:

```text
docs/week1-report.md
docs/week2-report.md
docs/worklog/week1.md
docs/worklog/week2.md
docs/ai-declaration.md
```

Điền các ô `[điền]` bằng dữ liệu thật trước khi nộp.

## 4. Kiểm tra evidence

Local hiện có:

```text
screenshots/week1/
screenshots/week2/khoi/
```

Bộ 19 ảnh phía Quân cần được đồng bộ từ branch/PR tài liệu Tuần 2 nếu muốn main chứa đầy đủ evidence của cả hai thành viên.

## 5. Push Git

Trong repository local đang liên kết GitHub:

```powershell
git switch main
git pull origin main
git status
```

Copy nội dung package đã chỉnh vào repository, sau đó:

```powershell
git status
git diff
python -m pytest -q
git add README.md docs screenshots src tests scripts iac .gitignore
git commit -m "docs: organize detailed week1 and week2 submission"
git push origin main
```

Nếu nhóm không cho push trực tiếp `main`, tạo branch mới và Pull Request.

## 6. Nộp

Chỉ coi là sẵn sàng nộp khi:

- source/tests PASS;
- báo cáo Tuần 1/Tuần 2 rõ ràng;
- worklog đủ ≥ 8 giờ thực tế/người/tuần;
- khai báo AI đúng thực tế;
- evidence truy cập được;
- GitHub Public và link không lỗi.
