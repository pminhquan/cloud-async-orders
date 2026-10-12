# Báo cáo tiến độ Tuần 1

## 1. Công việc đã làm trong tuần

| STT | Công việc | Mức độ hoàn thành |
|---|---|---:|
| 1 | Tìm hiểu vai trò của API Gateway, Lambda, DynamoDB và SNS trong kiến trúc Serverless | 100% |
| 2 | Tạo DynamoDB table `Orders` với partition key `orderId` | 100% |
| 3 | Cấu hình DynamoDB ở chế độ On-demand | 100% |
| 4 | Tạo Lambda `order-producer` bằng Python và sử dụng `LabRole` | 100% |
| 5 | Cấu hình Lambda với Memory 128 MB và Timeout 10 giây | 100% |
| 6 | Xây dựng PoC Producer Lambda để nhận dữ liệu đơn hàng, sinh `orderId` và trả trạng thái `PENDING` | 100% |
| 7 | Kiểm thử Lambda và nhận kết quả `statusCode = 202` | 100% |
| 8 | Tạo HTTP API Gateway `order-api` | 100% |
| 9 | Tạo route `POST /orders` tích hợp với Lambda `order-producer` | 100% |
| 10 | Kiểm thử API bằng PowerShell và nhận HTTP `202 Accepted` | 100% |
| 11 | Tạo SNS topic `order-dlq-alert` loại Standard | 100% |
| 12 | Tạo Email Subscription và xác nhận trạng thái `Confirmed` | 100% |
| 13 | Gắn tag `Project = AsyncOrderProcessing`, `Owner = Khoi-Quan` cho các tài nguyên đã triển khai | 80% |
| 14 | Lưu mã nguồn, dữ liệu test và ảnh minh chứng để đưa lên GitHub | 100% |

### Ghi chú phạm vi Tuần 1
Tuần 1 là giai đoạn làm quen dịch vụ và dựng nền tảng. Producer Lambda hiện mới ở mức PoC: nhận request và trả HTTP `202 Accepted`; chưa gọi `SQS SendMessage`. Việc thống nhất JSON giữa hai thành viên và tích hợp Producer → SQS → Consumer sẽ thực hiện ở Tuần 2.

## 2. Minh chứng

- **Hình 1:** DynamoDB `Orders` ở trạng thái `Active`, partition key `orderId`, chế độ On-demand.
- **Hình 2:** Lambda `order-producer` thực thi PoC thành công và trả về HTTP `202`.
- **Hình 3:** API Gateway `order-api` có route `POST /orders`.
- **Hình 4:** Kiểm thử API bằng PowerShell, nhận HTTP `202 Accepted` và dữ liệu đơn hàng trạng thái `PENDING`.
- **Hình 5:** SNS topic `order-dlq-alert` được tạo thành công.
- **Hình 6:** Email Subscription của SNS ở trạng thái `Confirmed`.

## 3. Các việc sẽ làm trong tuần tiếp theo

- Thống nhất cấu trúc JSON/message giữa Producer và Consumer khi bắt đầu tích hợp chung.
- Thống nhất tài khoản/Learner Lab dùng để dựng luồng tích hợp của nhóm.
- Tích hợp Lambda `order-producer` với SQS và thực hiện `SendMessage`.
- Hoàn thiện Consumer Lambda để nhận và xử lý message từ SQS theo batch.
- Kết nối Consumer Lambda với DynamoDB `Orders`.
- Kiểm thử luồng lõi: `API Gateway → Producer Lambda → SQS → Consumer Lambda → DynamoDB`.
- Ghi nhận log trên CloudWatch và cập nhật source code/tài liệu lên GitHub.

> Các phần cảnh báo nâng cao như CloudWatch Alarm, kiểm thử DLQ/retry đầy đủ và tối ưu giám sát sẽ tiếp tục ở giai đoạn sau theo kế hoạch môn học.

## 4. Link GitHub public của nhóm

```text
https://github.com/pminhquan/cloud-async-orders
```

Đảm bảo repository ở chế độ **Public** để giảng viên có thể truy cập.

## 5. AI hỗ trợ

Trong Tuần 1, nhóm có sử dụng ChatGPT để tham khảo kiến trúc, hướng dẫn cấu hình AWS, hỗ trợ viết mã Lambda PoC và gỡ lỗi trong quá trình kiểm thử. Toàn bộ tài nguyên được triển khai và kiểm thử trực tiếp trên AWS Learner Lab. Nhóm chịu trách nhiệm hiểu và giải thích các cấu hình, mã nguồn và luồng xử lý khi vấn đáp.
