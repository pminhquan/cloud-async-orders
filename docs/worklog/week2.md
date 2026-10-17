# Worklog Tuần 2

> **Xác nhận tiến độ của nhóm (17/10/2026):** Nhóm báo cáo cả Quân và Khôi đã đáp ứng mức tối thiểu **8 giờ/người trong Tuần 2**. Đây là xác nhận của người nộp, **không phải số giờ được kiểm toán**. Ngày làm, giờ làm từng hoạt động và tổng có phép cộng vẫn chưa được cung cấp; không tạo bảng thời gian giả. Nếu GV yêu cầu bảng giờ, hai thành viên cần điền nhật ký thật.

## 1. Quy tắc

- Mỗi thành viên tối thiểu 8 giờ thực tế.
- Chỉ ghi thời gian thực tế đã làm.
- Không suy số giờ từ timestamp commit, ảnh, CloudWatch hoặc AI.

## 2. Phạm Minh Quân

| Hoạt động | Kết quả/minh chứng | Ngày | Số giờ thực tế |
|---|---|---|---:|
| Nâng cấp Consumer + DynamoDB | PR #5 / source Consumer | Chưa tổng hợp | Chưa tổng hợp |
| Idempotency + conflict | tests + AWS evidence | Chưa tổng hợp | Chưa tổng hợp |
| Unit tests Consumer | 15/15 PASS | Chưa tổng hợp | Chưa tổng hợp |
| Full E2E | API → DynamoDB PROCESSED | Chưa tổng hợp | Chưa tổng hợp |
| Invalid JSON → Retry → DLQ | CloudWatch + DLQ | Chưa tổng hợp | Chưa tổng hợp |
| Batch valid/mixed/replay | direct Lambda tests | Chưa tổng hợp | Chưa tổng hợp |
| Small load 10 request | 10/10 `202`; 10 `PROCESSED` | Chưa tổng hợp | Chưa tổng hợp |
| Evidence + tài liệu | PR #6 | Chưa tổng hợp | Chưa tổng hợp |
| **Tổng** |  |  | **Chưa có bảng phân bổ giờ chi tiết** |

## 3. Nguyễn Đoàn Minh Khôi

| Hoạt động | Kết quả/minh chứng | Ngày | Số giờ thực tế |
|---|---|---|---:|
| Producer → SQS | Producer source / Lambda test | Chưa tổng hợp | Chưa tổng hợp |
| Input validation | PR #7 / tests | Chưa tổng hợp | Chưa tổng hợp |
| Test valid/invalid | `screenshots/week2/khoi/` | Chưa tổng hợp | Chưa tổng hợp |
| Invalid không enqueue | SQS before/after | Chưa tổng hợp | Chưa tổng hợp |
| Kiểm tra queue backlog/DLQ | ảnh kiểm tra message | Chưa tổng hợp | Chưa tổng hợp |
| Chuẩn hóa evidence/repository | screenshot README/docs | Chưa tổng hợp | Chưa tổng hợp |
| Báo cáo Tuần 2 / AI declaration | `docs/week2-report.md` | Chưa tổng hợp | Chưa tổng hợp |
| **Tổng** |  |  | **Chưa có bảng phân bổ giờ chi tiết** |

## 4. Trạng thái trước nộp

Người nộp xác nhận nhóm đạt ngưỡng tối thiểu 8 giờ/người trong Tuần 2. Đây là xác nhận ở mức tổng hợp; ngày/giờ thực tế chưa được cung cấp để đối soát độc lập. Nếu giảng viên yêu cầu chi tiết, mỗi thành viên bổ sung bảng thời lượng thật.
