# Công việc và minh chứng Tuần 2

## Phạm Minh Quân

| Hoạt động | Kết quả/minh chứng |
| --- | --- |
| Nâng cấp Consumer + DynamoDB | PR #5 / source Consumer |
| Idempotency + conflict | tests + AWS evidence |
| Unit tests Consumer | 15/15 PASS |
| Full E2E | API → DynamoDB PROCESSED |
| Invalid JSON → Retry → DLQ | CloudWatch + DLQ |
| Batch valid/mixed/replay | direct Lambda tests |
| Small load 10 request | 10/10 `202`; 10 `PROCESSED` |
| Evidence + tài liệu | PR #6 |

## Nguyễn Đoàn Minh Khôi

| Hoạt động | Kết quả/minh chứng |
| --- | --- |
| Producer → SQS | Producer source / Lambda test |
| Input validation | PR #7 / tests |
| Test valid/invalid | `screenshots/week2/khoi/` |
| Invalid không enqueue | SQS before/after |
| Kiểm tra queue backlog/DLQ | ảnh kiểm tra message |
| Chuẩn hóa evidence/repository | screenshot README/docs |
| Báo cáo Tuần 2 / AI declaration | `docs/week2-report.md` |
