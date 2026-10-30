# Khai báo sử dụng AI — Bốn tuần

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda
**Môn học:** CLC0332779_05UTExMC — Điện toán đám mây
**Nhóm:** Serverless

## 1. Công cụ theo thành viên

| Thành viên | Công cụ | Model | Phạm vi hỗ trợ |
|---|---|---|---|
| Nguyễn Đoàn Minh Khôi (24110259) | ChatGPT | GPT-5.6 Sol | Producer Lambda, API Gateway, validation, SNS, xử lý lỗi AWS, minh chứng và báo cáo |
| Phạm Minh Quân (24110311) | ChatGPT | GPT-6.0 (thành viên cung cấp) | Consumer Lambda, DynamoDB, idempotency, `ORDER_CONFLICT`, SQS trigger, retry/DLQ, unit test, E2E, batch/load và tài liệu |

Model của Quân do thành viên tự xác nhận; nhóm không đối chiếu độc lập lịch sử hội thoại.

## 2. Phạm vi hỗ trợ Tuần 1–2

- **Khôi:** giải thích vai trò API Gateway, Lambda, SQS, DynamoDB, SNS; gợi ý `boto3`, `send_message()`, validation `202/400/500`, Lambda Test Event và cách đối soát invalid request không enqueue.
- **Quân:** gợi ý xử lý SQS `Records`, parse/validate JSON, conditional `PutItem`, `ConsistentRead=True`, phân biệt replay với `ORDER_CONFLICT`, cấu hình Event Source Mapping, retry/redrive/DLQ, test batch/replay, E2E và small load.
- AI cung cấp giải thích, ví dụ code/JSON và phương án kiểm thử để tham khảo. Nhóm trực tiếp triển khai, cấu hình, chạy thử, đối soát dữ liệu và chụp minh chứng.

## 3. Phạm vi hỗ trợ Tuần 3–4

- Hỗ trợ công cụ benchmark/load/metrics, template monitoring, unit tests, CI, rà soát và trình bày tài liệu.
- Ngày 29/10/2026, Codex hỗ trợ đối chiếu source và thao tác qua phiên Console/CloudShell của Lab Quân do sinh viên đăng nhập: cập nhật deployment Producer từ source `main`, bật Event Source Mapping đúng nguồn, chạy E2E/validation/replay/conflict có giới hạn và quan sát một phép thử retry. Các thao tác này không được trình bày là sinh viên tự thực hiện thủ công.
- Antigravity Desktop hỗ trợ rà soát offline, kiểm thử và công cụ trình bày tài liệu; không thay đổi source, test, script hay IaC của ứng dụng.
- Ngày 30/10/2026, Codex hỗ trợ kiểm kê AWS qua CloudShell, thu log/metrics và ảnh gốc, chạy kiểm thử và cập nhật tài liệu. Sau phê duyệt của chủ Lab, hỗ trợ bật mapping Consumer và triển khai SNS cùng một alarm DLQ từ template hiện có.
- AI hỗ trợ tổng hợp inventory, phân tích kết quả B1/B2/B3, tra nguồn giá AWS và soạn báo cáo/kịch bản. Không có giao diện Console hoặc kết quả đo nào được tạo lại.

## 4. Trách nhiệm của nhóm

- Thao tác AWS Learner Lab tại `us-east-1`, dùng `LabRole`, trực tiếp tạo/cấu hình tài nguyên.
- Chạy test, kiểm tra CloudWatch Logs, SQS/DLQ, DynamoDB và API; chụp, phân loại ảnh minh chứng.
- Review source, tests, tài liệu; tạo commit/PR và đối soát kết quả trên `main`.
- Chịu trách nhiệm giải thích mã nguồn, phương pháp và số liệu khi trình bày.

## 5. Đối chiếu và giới hạn

- Kết quả được xác minh bằng source, unit tests, log/ảnh AWS và JSON/CSV trong `docs/evidence/`.
- Full E2E, retry/DLQ, conflict, batch/replay và load Tuần 2 chạy trên Lab Quân; validation Producer và quan sát SQS ghi nhận trên Lab Khôi.
- Batch nhiều record Tuần 2 là direct Lambda invocation, không phải bằng chứng SQS gom batch lớn hơn 1. Kết quả B2/B3 Tuần 3 ngày 24/10 là batch thật trong phạm vi mẫu nhỏ.
- Alarm → SNS → email Tuần 3 là phép thử thủ công trên Lab Khôi, không chứng minh DLQ metric tự kích hoạt cảnh báo.
- Khai báo này không thay thế dữ liệu kiểm thử hoặc minh chứng AWS.

**Mã nguồn và minh chứng:** [Producer](../src/producer/lambda_function.py) · [Consumer](../src/consumer/lambda_function.py) · [Minh chứng Tuần 1](evidence/week1/README.md) · [Tuần 2](evidence/week2/README.md) · [Tuần 3](evidence/week3/README.md) · [Tuần 4](evidence/week4/README.md).
