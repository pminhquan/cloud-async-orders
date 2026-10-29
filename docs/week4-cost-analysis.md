# Đánh giá chi phí và quản lý tài nguyên

Đề tài dùng API Gateway → Lambda Producer → SQS → Lambda Consumer → DynamoDB; CloudWatch và SNS hỗ trợ giám sát. Phân tích dưới đây căn cứ cấu trúc triển khai của repo và trang giá chính thức AWS đã truy cập ngày 29/10/2026. Đây là mô hình chi phí, không phải hóa đơn thanh toán của Learner Lab.

## 1. Thành phần chi phí

| Dịch vụ | Đại lượng cần theo dõi | Hướng tối ưu phù hợp bài thực hành |
|---|---|---|
| API Gateway | Loại API, số request, dữ liệu truyền ra; REST API có thể có cache tính phí riêng | Giữ loại API đang dùng, không bật cache hoặc thêm stage khi chưa có nhu cầu; validation sớm ở Producer giảm công việc hạ nguồn. [Nguồn](https://aws.amazon.com/api-gateway/pricing/) |
| Lambda | Số invocation và tài nguyên tính toán theo memory × thời gian; retry làm tăng số lần thực thi | Dùng duration thực tế để cân nhắc memory/timeout; batch giảm số invocation nhưng cần xét full-batch retry; không bật provisioned concurrency cho demo nhỏ. [Nguồn](https://aws.amazon.com/lambda/pricing/) |
| SQS | Các thao tác gửi, nhận, xóa, đổi visibility và kích thước payload; payload được định lượng theo khối 64 KB | Tránh polling thủ công lặp lại; dùng ESM và batch hợp lý; không tái benchmark chỉ để có thêm ảnh. Standard/FIFO có cơ chế giá riêng. [Nguồn](https://aws.amazon.com/sqs/pricing/) |
| DynamoDB | Capacity mode, kích thước item, thao tác đọc/ghi và lưu trữ; strong read có mức tiêu thụ khác eventual read | Giữ conditional write và strong read ở nhánh duplicate để bảo đảm đúng dữ liệu; không đổi cơ chế consistency chỉ để giảm chi phí. Đánh giá capacity theo tải thật. [Nguồn](https://aws.amazon.com/dynamodb/pricing/) |
| CloudWatch | Log ingestion/lưu trữ, truy vấn log, metric tùy chỉnh và alarm | Dùng log có cấu trúc gọn, lọc theo runId và khoảng thời gian ngắn. Chỉ giảm retention sau khi bảo toàn minh chứng và được phép vì có thể làm mất log cũ. [Nguồn](https://aws.amazon.com/cloudwatch/pricing/) |
| SNS | Publish request, dung lượng và giao thức/số lượng notification delivery | Chỉ thử một chuỗi cảnh báo có ý nghĩa; tránh publish liên tục hoặc tạo subscription trùng. Không đồng nhất publish thành công với email đã tới hộp thư. [Nguồn](https://aws.amazon.com/sns/pricing/) |

## 2. Phương pháp ước lượng có thể tái lập

Với `N` đơn hợp lệ, pipeline bình thường tạo khoảng `N` lần gọi API và Producer. Số lần gọi Consumer phụ thuộc cách SQS gom batch, lỗi và retry; không lấy `N / BatchSize` làm số đo thực tế khi chưa kiểm tra batch đầy. Cần tính cả thao tác SQS, conditional write thất bại và strong read khi phát lại. Chi phí log và cảnh báo được xét riêng.

Công thức tính phần thời gian Lambda là tổng `memory_GB × billed_duration_seconds` của từng invocation, nhân đơn giá áp dụng cho Region/kiến trúc. Không dùng timeout cấu hình thay cho duration bị tính phí. Với DynamoDB, số request nghiệp vụ không tự bằng số đơn vị capacity vì kích thước item và consistency ảnh hưởng mức tiêu thụ.

Mọi ước lượng định lượng cần ghi rõ Region, thời điểm tra giá, số request, dung lượng, memory, billed duration, capacity mode và điều kiện ưu đãi. Không mặc định Learner Lab được áp dụng Free Tier như tài khoản AWS cá nhân. Chỉ số ngân sách trên màn hình Lab hoặc widget Console là quan sát tại một thời điểm, không thay cho hóa đơn có phân bổ theo dịch vụ.

## 3. Quyết định cho phạm vi đề tài

Ưu tiên tránh tác vụ thừa: tái sử dụng benchmark B1, load B2 và batch B3 đã có provenance; acceptance Tuần 4 dùng tập dữ liệu nhỏ có định danh riêng. Giữ cơ chế idempotency, validation và giới hạn concurrency 10 của Lab. Không thay Standard bằng FIFO, thêm dịch vụ hoặc đổi capacity chỉ để trình bày là đã tối ưu.

Danh sách KEEP/REVIEW và trạng thái cuối của tài nguyên được ghi cùng inventory Tuần 4. Queue chính, DLQ lịch sử, bảng Orders, log và tài nguyên phục vụ demo được giữ. Xóa queue benchmark hoặc dữ liệu thử chỉ được làm khi có phê duyệt cụ thể và đã bảo toàn minh chứng. Báo cáo chỉ nhận là đã giảm chi phí khi có dữ liệu trước/sau cùng điều kiện đo.
