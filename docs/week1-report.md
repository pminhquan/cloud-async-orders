# BÁO CÁO TIẾN ĐỘ TUẦN 1

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**GVHD:** Huỳnh Xuân Phụng  
**Region sử dụng:** `us-east-1`

## 1. Phân chia công việc tuần 1

| STT | Công việc | Nội dung chính | Người thực hiện |
|---:|---|---|---|
| 1 | Tìm hiểu dịch vụ | Tìm hiểu SQS Standard/FIFO, DLQ, Lambda, API Gateway, DynamoDB, CloudWatch và SNS; nắm vai trò từng dịch vụ trong mô hình bất đồng bộ. | Khôi, Quân |
| 2 | Thiết kế kiến trúc | Xác định luồng đích `API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB`, kèm nhánh lỗi `DLQ → CloudWatch Alarm → SNS`. | Khôi, Quân |
| 3 | Vẽ sơ đồ kiến trúc | Vẽ sơ đồ tổng thể, phân biệt luồng đã PoC trong Tuần 1 và luồng tích hợp dự kiến ở các tuần sau. | Quân, Khôi góp ý |
| 4 | PoC Queue/Consumer | Tạo và kiểm thử SQS Standard, DLQ, Consumer Lambda; thử message hợp lệ, message lỗi và retry/DLQ ở mức PoC. | Quân |
| 5 | PoC API/Producer | Tạo DynamoDB `Orders`, Lambda `order-producer`, HTTP API `order-api`, route `POST /orders`; kiểm thử Lambda/API trả `202`. | Khôi |
| 6 | Cảnh báo ban đầu | Tạo SNS topic `order-dlq-alert` và Email Subscription ở trạng thái `Confirmed`. | Khôi |
| 7 | Tài liệu và GitHub | Chuẩn hóa source, tài liệu, ảnh minh chứng, quy ước tag và repository public. | Khôi, Quân |

## 2. Mức độ hoàn thành tuần 1

| STT | Công việc | Kết quả đạt được | Mức độ |
|---:|---|---|---:|
| 1 | Nghiên cứu dịch vụ | Đã nắm vai trò các dịch vụ chính và các ràng buộc của Learner Lab. | 100% |
| 2 | Kiến trúc hệ thống | Đã xác định kiến trúc tổng thể và tách rõ Producer, Queue, Consumer, Database và nhánh lỗi. | 100% |
| 3 | Sơ đồ kiến trúc | Đã có sơ đồ tổng thể phục vụ báo cáo và tích hợp ở tuần sau. | 100% |
| 4 | SQS/DLQ/Consumer PoC | Đã kiểm thử độc lập SQS → Consumer và retry/DLQ; chưa tích hợp E2E với Producer/DynamoDB. | 90% |
| 5 | API/Producer PoC | Đã kiểm thử `POST /orders` qua API Gateway → Producer Lambda và nhận HTTP `202 Accepted`. | 100% |
| 6 | DynamoDB | Đã tạo bảng `Orders` với partition key `orderId`, chế độ On-demand. | 100% |
| 7 | SNS | Đã tạo `order-dlq-alert` và xác nhận Email Subscription. | 100% |
| 8 | Tích hợp toàn hệ thống | Hai PoC đang chạy riêng; chưa ghép `Producer → SQS → Consumer → DynamoDB`. | 50% |
| 9 | GitHub/tài liệu | Đã có source, tài liệu kỹ thuật và ảnh minh chứng Tuần 1. | 100% |

## 3. Công việc tuần tiếp theo

- Thống nhất JSON/message giữa Producer và Consumer.
- Thống nhất môi trường/tài khoản dùng để tích hợp chung.
- Cho Producer gửi message thật vào SQS.
- Hoàn thiện Consumer đọc message theo batch và ghi DynamoDB.
- Kiểm thử luồng lõi `API Gateway → Producer → SQS → Consumer → DynamoDB`.
- Tiếp tục ghi log CloudWatch và cập nhật source/minh chứng lên GitHub.

Các phần cảnh báo hoàn chỉnh bằng CloudWatch Alarm, tối ưu retry/DLQ, IaC và load test sẽ làm theo tiến độ Tuần 3–4.

## 4. GitHub Public

Repository nhóm:

`https://github.com/pminhquan/cloud-async-orders`

## 5. AI hỗ trợ

Nhóm sử dụng ChatGPT để tham khảo kiến trúc, cách cấu hình dịch vụ AWS, mã Lambda PoC, dữ liệu JSON test, lệnh PowerShell và cách tổ chức tài liệu. Nhóm trực tiếp triển khai và kiểm thử trên AWS Learner Lab, tự đối chiếu kết quả thực tế và điều chỉnh nội dung trước khi nộp.
