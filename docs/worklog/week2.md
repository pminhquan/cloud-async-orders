# Worklog Tuần 2

## 1. Quy tắc

- Mỗi thành viên tối thiểu 8 giờ thực tế.
- Chỉ ghi thời gian thực tế đã làm.
- Không suy số giờ từ timestamp commit, ảnh, CloudWatch hoặc AI.

## 2. Phạm Minh Quân

| Hoạt động | Kết quả/minh chứng | Ngày | Số giờ thực tế |
|---|---|---|---:|
| Nâng cấp Consumer + DynamoDB | PR #5 / source Consumer | [điền] | [điền] |
| Idempotency + conflict | tests + AWS evidence | [điền] | [điền] |
| Unit tests Consumer | 15/15 PASS | [điền] | [điền] |
| Full E2E | API → DynamoDB PROCESSED | [điền] | [điền] |
| Invalid JSON → Retry → DLQ | CloudWatch + DLQ | [điền] | [điền] |
| Batch valid/mixed/replay | direct Lambda tests | [điền] | [điền] |
| Small load 10 request | 10/10 `202`; 10 `PROCESSED` | [điền] | [điền] |
| Evidence + tài liệu | PR #6 | [điền] | [điền] |
| **Tổng** |  |  | **[điền, phải ≥ 8]** |

## 3. Nguyễn Đoàn Minh Khôi

| Hoạt động | Kết quả/minh chứng | Ngày | Số giờ thực tế |
|---|---|---|---:|
| Producer → SQS | Producer source / Lambda test | [điền] | [điền] |
| Input validation | PR #7 / tests | [điền] | [điền] |
| Test valid/invalid | `screenshots/week2/khoi/` | [điền] | [điền] |
| Invalid không enqueue | SQS before/after | [điền] | [điền] |
| Kiểm tra queue backlog/DLQ | ảnh kiểm tra message | [điền] | [điền] |
| Chuẩn hóa evidence/repository | screenshot README/docs | [điền] | [điền] |
| Báo cáo Tuần 2 / AI declaration | `docs/week2-report.md` | [điền] | [điền] |
| **Tổng** |  |  | **[điền, phải ≥ 8]** |

## 4. Trạng thái trước nộp

Worklog này cố ý để trống ngày/giờ vì chưa có số liệu thực tế được xác nhận trong repository. Hai thành viên phải điền trước khi nộp nếu đây là điều kiện bắt buộc của form giảng viên.
