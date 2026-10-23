# Hướng dẫn evidence Tuần 3

Bảng này mô tả loại bằng chứng và dữ liệu cần quan sát cho từng kịch bản. Tên ảnh là quy ước lưu trữ; kết quả báo cáo lấy từ evidence thực tế tương ứng.

| Kịch bản | Tên ảnh gợi ý | Dữ liệu cần quan sát |
| --- | --- | --- |
| SNS subscription | `W3-SNS-Topic-Subscription-Confirmed.png` | Topic, protocol, subscription confirmation; che email/ARN/account. |
| DLQ alarm configuration | `W3-CW-DLQ-Alarm-Config.png` | AWS/SQS, ApproximateNumberOfMessagesVisible, QueueName, threshold, evaluation periods, missing-data, SNS action. |
| Alarm transition | `W3-CW-DLQ-Alarm-Triggered-ALARM.png` | Alarm history, datapoint, trạng thái kỹ thuật và UTC timestamps của cùng lần thử. |
| SNS email | `W3-SNS-Email-Notification-Received.png` | Nội dung mail khớp alarm và thời điểm; che thông tin người nhận. |
| Dedicated benchmark queues | `W3-Bench-Queues-Isolated.png` | Tên và loại Standard/FIFO, tách khỏi queue chính. |
| Standard API benchmark | `W3-Bench-Standard-CLI-Summary.png` | runId, cấu hình count/rate/batch/timeout, attempted/accepted/failed, unique/duplicate/completeness, latency và throughput. |
| FIFO single group | `W3-Bench-FIFO-SingleGroup-CLI-Summary.png` | runId, groupCount=1, ordering theo group, dedup, cùng bộ thống kê. |
| FIFO multi group | `W3-Bench-FIFO-MultiGroup-CLI-Summary.png` | runId, groupCount, ordering từng group và số đo so sánh, không định trước throughput tốt hơn. |
| API load | `W3-Load-API-Summary.png` | runId, requestId, HTTP status, responseTimeMs, orderId, loại lỗi. |
| DynamoDB reconciliation | `W3-Load-DynamoDB-Reconciliation.png` | Cùng runId/orderId, GetItem result/status, số query và thời gian quan sát; tách khỏi HTTP 202. |
| CloudWatch metrics | `W3-Metrics-Collector-CloudWatch-Summary.png` | UTC window, namespace/dimension/statistic, raw datapoints và giá trị tổng hợp. |
| Local tests | `W3-Local-Tests.txt` | Commit SHA, Python/dependency versions, command, pass/fail/skip và exit code thực tế. |
| GitHub Actions | `W3-CI.png` | Workflow run URL, head SHA, job và conclusion thực tế. |

Quân phụ trách chính monitoring, benchmark, load/reconciliation và kỹ thuật; Khôi phối hợp SNS/email, Producer/API và review theo [phân công](../../task-assignment.md). Người cung cấp evidence xác định người thao tác và thời gian của chính lần thực hiện đó.

Giữ JSON/CSV cùng runId để đối chiếu với ảnh; phân biệt CloudWatch, SQS API, API load, DynamoDB và unit test/mock. Không lấy ảnh Tuần 1–2 thay cho một lần đo Tuần 3. Che account ID, ARN cá nhân, queue URL, endpoint riêng, email; không lưu credentials, token, cookie hoặc receipt handle. Ví dụ synthetic phải được ghi rõ SYNTHETIC SAMPLE.

Quy trình thao tác xem [runbook](../../week3-aws-manual-runbook.md). Các thao tác ghi chỉ được thực hiện trong đúng phạm vi được owner cho phép; không purge queue hoặc sửa/xóa DynamoDB data.
