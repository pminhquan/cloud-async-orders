# Minh chứng Tuần 4 — 29/10/2026

## 1. Nguồn dữ liệu

- [Báo cáo nghiệm thu AWS](../../week4-report.md): inventory, đối chiếu deployment, ma trận E2E/validation/replay/conflict, log retry và metrics của Lab Quân ngày 29/10.
- [Kiểm thử offline](offline-validation.md): phương pháp, lệnh và đầu ra hồi quy mô phỏng dịch vụ.
- [Báo cáo cuối kỳ](../../final-report.md): tổng hợp kết quả và giới hạn kỹ thuật.
- [Ma trận nghiệm thu](../../week4-execution.md): dẫn chiếu tiêu chí và kết quả.

Số liệu AWS Tuần 4 là bản ghi quan sát có chọn lọc trong báo cáo, không phải raw export đính kèm. Phạm vi chứng cứ được giữ rõ: HTTP 202 được đối chiếu với item PROCESSED; redrive được suy luận từ cấu hình, năm log cùng messageId và biến đổi số lượng, không đọc body DLQ.

## 2. Minh chứng lịch sử ngày 24/10/2026

- B1: [Standard, 20 message](../week3/quan/b1-2026-10-24/standard/benchmark-summary.json), [FIFO 1 group](../week3/quan/b1-2026-10-24/fifo-single/benchmark-summary.json), [FIFO 5 group](../week3/quan/b1-2026-10-24/fifo-multi/benchmark-summary.json).
- B2: [Load và đối soát 10 đơn](../week3/quan/b2-2026-10-24/load/load-test-summary.json).
- B3: [Hai record cùng invocation](../week3/quan/b3-2026-10-24/batch-proof.json), [ảnh CloudWatch thật](../week3/quan/b3-2026-10-24/screenshots/W3-B3-CloudWatch-Two-Record-Batch.jpg).
- Khôi: [Phạm vi SNS/Alarm](../../week3-khoi-evidence.md), [Alarm History](../week3/khoi/W3-CW-DLQ-Alarm-History.png), [email cảnh báo](../week3/khoi/W3-SNS-Alarm-Email-Received.png).

Minh chứng Khôi xác nhận subscription, publish/email và manual Alarm State → SNS → email. Kết quả này không chứng minh DLQ metric tự kích hoạt email và không đại diện cho cấu hình hiện tại của Lab Quân.

## 3. Tính nguyên gốc và định danh học phần

Minh chứng sử dụng bản chụp gốc, giữ thông tin sinh viên và MSSV phục vụ đối chiếu học phần. Tám ảnh Khôi trùng byte với bản gốc đã lưu và ảnh trên nguồn tham chiếu; không thay đổi trạng thái, thời điểm hoặc nội dung kỹ thuật.

| Môi trường/minh chứng | Sinh viên | MSSV |
|---|---|---|
| Lab Quân, B1/B2/B3 và nghiệm thu Tuần 4 | Phạm Minh Quân | 24110311 |
| Lab Khôi, API/DynamoDB và SNS/Alarm lịch sử | Nguyễn Đoàn Minh Khôi | 24110259 |

Ảnh B2/B3 giữ nguyên bản crop đã có. Các ảnh được dẫn theo đúng ngày và môi trường, không trình bày như thao tác AWS mới hoặc giao diện mô phỏng.
