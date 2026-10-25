# KẾ HOẠCH TUẦN 4 — KIỂM THỬ TỔNG THỂ, TỐI ƯU CHI PHÍ, DỌN DẸP AWS VÀ DEMO

**Đề tài:** Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda  
**Nhóm:** Serverless  
**Môn học:** CLC0332779_05UTExMC – Điện toán đám mây  
**GVHD:** TS. Huỳnh Xuân Phụng  
**AWS Region:** `us-east-1`  
**Sinh viên:** Phạm Minh Quân (24110311), Nguyễn Đoàn Minh Khôi (24110259)  
**Repository:** https://github.com/pminhquan/cloud-async-orders  
**Trạng thái tài liệu:** Kế hoạch dự kiến cho Tuần 4; không phải báo cáo kết quả đã hoàn thành.

---

## 1. Mục tiêu

Tuần 4 là giai đoạn hoàn thiện đề tài bốn tuần. Nhóm tập trung: **(1)** kiểm thử tổng thể pipeline đơn hàng; **(2)** đối chiếu, tối ưu cấu hình và đánh giá chi phí sử dụng AWS; **(3)** dọn dẹp tài nguyên thử nghiệm có kiểm soát; **(4)** hoàn thiện tài liệu và trình diễn hệ thống. Tất cả kết quả nghiệm thu sẽ được bổ sung sau khi thực hiện, kèm thời điểm, môi trường, mã lần chạy và minh chứng thực tế.

Kế hoạch kế thừa kết quả Tuần 3: Benchmark Standard/FIFO 60/60 message; load B2 10/10 HTTP 202 và 10/10 DynamoDB `PROCESSED`; batch B3 2 message trong cùng một Lambda invocation; kết quả CloudWatch/SNS trên Lab Khôi; 56 tests, 114 subtests và GitHub Actions SUCCESS. Không coi các kết quả Tuần 3 là bằng chứng cho những phép thử chưa chạy ở Tuần 4.

## 2. Phạm vi, phân công và sản phẩm dự kiến

| Mã | Hạng mục | Công việc dự kiến | Phụ trách | Sản phẩm/minh chứng dự kiến |
|---|---|---|---|---|
| **W4-01** | Kiểm kê & kiểm tra trước demo | Kiểm tra AWS account/Region, API route, Lambda, ESM, queue/DLQ, bảng `Orders`, SNS và Alarm; xác nhận trạng thái trước kiểm thử. | Khôi, Quân | Bảng inventory và ảnh/trạng thái trước kiểm thử |
| **W4-02** | Kiểm thử tổng thể E2E | Gửi request hợp lệ qua `POST /orders`; đối soát `orderId` đến `Orders.status=PROCESSED`. | Khôi (API/Producer), Quân (SQS/Consumer/DB) | Test cases, request/response, CloudWatch Logs, bản ghi DynamoDB |
| **W4-03** | Validation, idempotency, retry/DLQ | Kiểm tra dữ liệu không hợp lệ, phát lại cùng `orderId`, conflict và lỗi Consumer trong phạm vi được phép. | Khôi (validation), Quân (Consumer/DLQ) | Bảng PASS/FAIL và minh chứng từng ca; nêu rõ ca chưa thực hiện |
| **W4-04** | CloudWatch & SNS tổng thể | Đối soát Alarm, Email Subscription, Logs và metric; chỉ thử redrive thật khi có quyền và môi trường an toàn. | Khôi, Quân | Ảnh Alarm/SNS, metrics JSON/CSV và phân biệt thử thủ công/tự động |
| **W4-05** | Hiệu năng & cấu hình | Rà soát benchmark/load/batch từ Tuần 3; thử bổ sung có giới hạn nếu được phép; đánh giá timeout, memory, batch, concurrency. | Quân | Bảng trước/sau, đề xuất thông số, dữ liệu đo thật nếu có |
| **W4-06** | Tối ưu chi phí | Kiểm kê Lambda, SQS, DynamoDB, CloudWatch, SNS, API Gateway; phân tích yếu tố tính phí và đề xuất giảm lãng phí. | Quân, Khôi | Bảng kiểm kê chi phí/cấu hình, nguồn dữ liệu và đề xuất tối ưu |
| **W4-07** | Dọn dẹp tài nguyên | Phân loại tài nguyên cần giữ cho demo và tài nguyên thử nghiệm có thể xóa; bảo vệ `orders-dlq`, dữ liệu `Orders`, logs. | Chủ tài khoản Lab thao tác; thành viên còn lại đối chiếu | Checklist trước/sau, bằng chứng xác nhận, danh sách tài nguyên giữ/xóa |
| **W4-08** | Kiểm thử hồi quy & GitHub | Chạy tests, rà soát CI, kiểm tra links, cập nhật tài liệu, commit và PR; không đưa credentials lên repo. | Quân, Khôi | Kết quả CI, danh sách link hợp lệ, PR/commit và bản tài liệu cuối |
| **W4-09** | Báo cáo & demo cuối kỳ | Tạo kịch bản demo, phân vai trình bày, chuẩn bị tình huống xử lý sự cố và báo cáo tổng kết. | Quân, Khôi | Báo cáo cuối kỳ, tài liệu demo, ảnh/log dự phòng và slide (nếu cần) |

## 3. Kế hoạch kiểm thử tổng thể

### 3.1. Điều kiện tiên quyết

- Chỉ thao tác trong AWS Learner Lab và tài khoản được người sở hữu cho phép; xác nhận Region `us-east-1`.
- Kiểm tra mã Producer đã triển khai có đồng bộ validation với source trong GitHub hay chưa. Tuần 3 từng ghi nhận khác biệt trên Lab Quân; **không mặc định đã sửa xong**.
- Kiểm tra Event Source Mapping của `order-consumer`. Cuối Phase B3, trigger trên Lab Quân đã được hoàn nguyên về `Disabled`; cần cấu hình phù hợp trước khi demo E2E.
- Xác minh không có bài load khác đang chạy, kiểm tra queue/DLQ và DynamoDB trước khi phát sinh đơn mới.

### 3.2. Ma trận test cases dự kiến

| Mã test | Kịch bản | Kết quả mong đợi | Minh chứng cần lưu |
|---|---|---|---|
| T4-01 | POST hợp lệ | HTTP `202`, trả `orderId`; bản ghi tương ứng đạt `PROCESSED` trong thời gian kiểm tra cho phép | Request/response, orderId, DynamoDB |
| T4-02 | POST thiếu trường/sai `quantity` | HTTP `400` trên phiên bản Producer đã được xác nhận có validation; không enqueue message mới | Response và đối soát SQS theo phạm vi an toàn |
| T4-03 | Idempotent replay cùng `orderId` và payload | Không tạo đơn thứ hai, không ghi đè trạng thái đã xử lý | Consumer logs, DynamoDB item |
| T4-04 | Cùng `orderId`, payload khác | Có phản hồi/ghi log `ORDER_CONFLICT`, không ghi đè dữ liệu cũ | Logs và đối chiếu DynamoDB |
| T4-05 | SQS batch thật | Có ít nhất hai record trong cùng invocation nếu môi trường và lịch demo cho phép | CloudWatch RequestId và hai messageId |
| T4-06 | Retry/DLQ an toàn | Ghi nhận retry/redrive theo cấu hình, không can thiệp message lịch sử; chỉ chạy khi được duyệt | CloudWatch Logs, SQS/DLQ, runId |
| T4-07 | CloudWatch Alarm → SNS Email | Email/Alarm history đúng kịch bản; phân biệt manual Alarm State với metric-based ALARM | Alarm History, SNS Email, thời gian |
| T4-08 | Tests & CI | Các bài kiểm thử hồi quy và GitHub Actions của commit nộp cuối chạy thành công | Link commit và CI run |

**Nguyên tắc ghi nhận:** HTTP `202` chỉ chứng minh API đã chấp nhận yêu cầu, không thay cho DynamoDB `PROCESSED`; direct Lambda Test Event không được gọi là bằng chứng SQS gom batch; số liệu `NO_DATA` không tự đổi thành `0`. Mỗi test được đánh dấu `PASS`, `FAIL`, `BLOCKED` hoặc `NOT RUN` sau khi chạy, không điền kết quả trước.

## 4. Đánh giá hiệu năng và tối ưu chi phí AWS

### 4.1. Rà soát hiệu năng

- Dùng dữ liệu B1/B2/B3 để lập baseline: throughput, latency P95, số request thành công, thời gian Consumer, Errors/Throttles và độ đầy queue.
- Chỉ đề xuất điều chỉnh `BatchSize`, `MaximumBatchingWindowInSeconds`, Lambda timeout/memory và giới hạn concurrency sau khi đối chiếu cấu hình từng Lab và nguy cơ tác động đến tải hiện có.
- Nếu được phép đo bổ sung, giữ thống nhất script và điều kiện so sánh; công bố rõ số lượng mẫu, phương pháp client tuần tự/đồng thời, thời điểm và Region.

### 4.2. Bảng rà soát chi phí

| Dịch vụ | Yếu tố ảnh hưởng chi phí cần kiểm tra | Hướng tối ưu dự kiến |
|---|---|---|
| Lambda | Invocations, duration, memory, concurrency | Giảm invocation thừa, lựa chọn memory/timeout phù hợp với số đo |
| SQS | Số request Send/Receive/Delete, polling, queue phụ | Tối ưu cách nhận/batch; xóa queue benchmark sau khi được duyệt |
| DynamoDB | Read/Write requests, capacity mode, lưu trữ | Chọn chế độ phù hợp phạm vi demo; dọn dữ liệu thử nghiệm theo quyền cho phép |
| CloudWatch | Log ingestion, log retention, Alarm và metric | Rà soát log retention, Alarm thử nghiệm không còn sử dụng |
| SNS | Publish, subscription và thông báo | Không gửi thử lặp lại không cần thiết; rà soát subscription |
| API Gateway | Số API requests và tài nguyên API | Hạn chế request không cần thiết, rà soát stage/route dùng cho demo |

**Phương pháp báo cáo:** Nếu Lab không cung cấp quyền xem chi phí thực tế, ghi rõ **“không có dữ liệu chi phí thanh toán”** và trình bày đánh giá theo cấu hình, số request và tài liệu giá công khai; không ghi số tiền ước tính là khoản đã bị tính phí.

## 5. Kế hoạch dọn dẹp tài nguyên (chỉ sau khi lưu minh chứng và hoàn tất demo)

| Nhóm tài nguyên | Hành động dự kiến | Điều kiện bắt buộc trước thao tác |
|---|---|---|
| `orders-benchmark-standard`, `orders-benchmark.fifo` | Đánh giá xóa nếu không còn dùng | Đã lưu JSON/CSV, xác nhận queue thử nghiệm riêng, owner duyệt |
| `orders-queue`, `orders-dlq` | Giữ cho demo; xem xét dọn sau nghiệm thu | **Không purge**, không xóa message lịch sử hoặc queue chính khi chưa được duyệt rõ |
| DynamoDB `Orders` | Giữ bản ghi minh chứng; cân nhắc chỉ xóa dữ liệu test do nhóm sở hữu | Có danh sách `orderId`, backup/evidence, owner duyệt; không xóa toàn bảng tùy tiện |
| Lambda Producer/Consumer, ESM | Ghi lại cấu hình trước/sau; vô hiệu hóa/xóa chỉ khi không cần demo | Đã lưu code/cấu hình, xác minh không còn xử lý dang dở, owner duyệt |
| CloudWatch Logs/Alarms | Rà soát Alarm thử nghiệm và retention | Đã lưu log/screenshot cần nộp, kiểm tra tác động giám sát |
| SNS Topic/subscription | Giữ tới khi demo cảnh báo xong; rà soát sau | Người sở hữu xác nhận không còn cần nhận thông báo |
| API Gateway | Giữ endpoint tới khi demo xong; cân nhắc dọn | Đã lưu thông tin route/integration và hoàn tất nghiệm thu |

**Quy trình:** (1) chụp trạng thái trước; (2) lập danh sách và phân loại `KEEP` / `REVIEW` / `DELETE-APPROVED`; (3) sao lưu minh chứng; (4) chủ Lab phê duyệt; (5) thao tác tối thiểu; (6) xác minh trạng thái sau; (7) ghi vào báo cáo và GitHub. Không công khai access key, token, account ID hoặc email cá nhân.

## 6. Báo cáo cuối kỳ và kịch bản demo

### 6.1. Nội dung báo cáo cuối kỳ

- Kiến trúc các dịch vụ và Integration Contract; Producer, Consumer, SQS/DLQ, DynamoDB.
- Các bài kiểm thử chức năng, idempotency/conflict, retry/DLQ và giới hạn từng AWS Learner Lab.
- Kết quả Standard/FIFO B1, Load B2, SQS batch B3, CloudWatch/SNS, CI và kết quả kiểm thử tổng thể Tuần 4.
- Phương pháp đánh giá/tối ưu chi phí, tình trạng dọn dẹp tài nguyên và các vấn đề còn tồn tại.
- Minh chứng AWS, link commit/PR, khai báo AI và phân công/Worklog theo thành viên.

### 6.2. Kịch bản demo dự kiến

| Bước | Nội dung trình diễn | Phụ trách dự kiến |
|---:|---|---|
| 1 | Giới thiệu kiến trúc, JSON schema và tài nguyên AWS | Khôi, Quân |
| 2 | API `POST /orders` hợp lệ/không hợp lệ, giải thích Producer | Khôi |
| 3 | SQS Trigger, Consumer và DynamoDB `PROCESSED` theo `orderId` | Quân |
| 4 | Retry/DLQ và CloudWatch Alarm/SNS Email, giải thích rõ phạm vi phép thử | Khôi, Quân |
| 5 | Báo cáo Standard/FIFO, load B2, batch B3 và metrics | Quân |
| 6 | CI, đánh giá chi phí, tài nguyên và kết luận | Quân, Khôi |

Chuẩn bị ảnh AWS, CloudWatch Logs và JSON/CSV đã lưu để dự phòng khi phiên Learner Lab hết hạn hoặc không thể demo live. Không trình bày minh chứng dự phòng như một lần chạy mới.

## 7. Tiến độ và tiêu chí nghiệm thu Tuần 4

| Giai đoạn | Trọng tâm | Sản phẩm cần bàn giao |
|---|---|---|
| Đầu tuần | Kiểm kê tài nguyên, xác minh cấu hình Producer/Consumer, thiết kế test cases | Inventory + ma trận test dự kiến |
| Giữa tuần | Kiểm thử tổng thể; phân tích hiệu năng và tối ưu chi phí | Kết quả PASS/FAIL, log/ảnh AWS, bảng chi phí/cấu hình |
| Trước demo | Chạy hồi quy, chuẩn bị báo cáo và kịch bản demo | CI run, báo cáo cuối kỳ, đường dẫn minh chứng |
| Sau demo/nghiệm thu | Dọn dẹp tài nguyên đã được duyệt, lưu trạng thái cuối | Checklist trước/sau và danh sách giữ/xóa |

**Tiêu chí nghiệm thu (C10 và tổng kết đề tài):**

1. Có báo cáo kiểm thử tổng thể với kịch bản, kết quả và minh chứng cụ thể.
2. Có đánh giá hiệu năng và phương án tối ưu có lý do, không tự suy diễn số liệu.
3. Có nội dung đánh giá/tối ưu chi phí AWS theo dữ liệu được phép truy cập.
4. Có checklist và kết quả xử lý tài nguyên SQS, DynamoDB, Lambda, CloudWatch, SNS/API Gateway; dọn dẹp an toàn sau demo.
5. Có báo cáo cuối kỳ, kịch bản demo và phương án minh chứng dự phòng.
6. Source, tài liệu, CI, PR/commit và các liên kết minh chứng nằm trên repository public; không lộ dữ liệu nhạy cảm.

## 8. Tài liệu tham chiếu trong repository

- [Kế hoạch Tuần 3](week3-plan.md)
- [Báo cáo kỹ thuật Tuần 3](week3-report.md)
- [Kết quả Benchmark B1](week3-quan-b1-results.md)
- [Minh chứng SNS/CloudWatch/API của Khôi](week3-khoi-evidence.md)
- [Minh chứng AWS Tuần 3](evidence/week3/)
- [Kiến trúc/hợp đồng dữ liệu](integration-contract.md)
- [Mã nguồn và các Pull Request](https://github.com/pminhquan/cloud-async-orders)

**Kết luận kế hoạch:** Tuần 4 tập trung hoàn thiện kiểm thử tổng thể, đánh giá hiệu năng và chi phí, dọn dẹp tài nguyên có kiểm soát sau demo và hoàn chỉnh báo cáo cuối kỳ. Các mục là công việc dự kiến; kết quả thực tế sẽ được cập nhật kèm minh chứng sau khi thực hiện.
