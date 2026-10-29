# Kịch bản và gói quay demo cuối kỳ

**Thời lượng mục tiêu:** 9 phút 20 giây, tối đa 10 phút. Đây là storyboard, lời dẫn và checklist quay; chưa phải video đã ghi hoặc render. **Người trình bày:** Khôi — API/Producer/SNS; Quân — SQS/Consumer/DynamoDB, reliability và hiệu năng.

## 1. Timeline và thao tác màn hình

| Thời gian | Người | Hình ảnh/hành động | Nội dung chính |
|---|---|---|---|
| 00:00–00:40 | Khôi | Trang đầu báo cáo, tên đề tài/thành viên | Vấn đề và mục tiêu |
| 00:40–01:40 | Quân | Sơ đồ trong final-report.md | Luồng chính, vai trò queue và ranh giới 202/PROCESSED |
| 01:40–02:40 | Khôi | Producer `_validate`, request/response; dùng bản ghi Tuần 4 hoặc đúng một POST hợp lệ khi quay live | Contract và tiếp nhận đơn |
| 02:40–03:40 | Quân | ESM Enabled; tìm đúng orderId trong Orders và log Consumer | Đối soát xử lý thành công |
| 03:40–04:45 | Khôi | Bảng 12 ca invalid đã chạy; minh họa 400 có sẵn | Validation và không enqueue |
| 04:45–06:00 | Quân | Conditional PutItem/strong read; kết quả replay/conflict, năm mốc log retry và số lượng DLQ | Độ tin cậy và bảo vệ dữ liệu |
| 06:00–07:05 | Khôi | CloudWatch metrics Tuần 4; ảnh SNS/Alarm của Lab Khôi có nhãn 24/10 | Monitoring và giới hạn hai Lab |
| 07:05–08:10 | Quân | Bảng B1/B2/B3; ảnh CloudWatch B3 | Hiệu năng, batch thật, giới hạn mẫu |
| 08:10–09:00 | Quân | Bảng yếu tố chi phí và KEEP/REVIEW | Tối ưu có căn cứ, không xóa tài nguyên tùy tiện |
| 09:00–09:20 | Khôi + Quân | Kết luận, test summary/CI, repository | Kết quả và hướng phát triển |

## 2. Lời dẫn tiếng Việt

### 00:00–00:40 — Khôi

“Nhóm em gồm Nguyễn Đoàn Minh Khôi và Phạm Minh Quân, thực hiện đề tài xử lý đơn hàng bất đồng bộ bằng AWS Serverless. Bài toán là tiếp nhận đơn nhanh nhưng vẫn bảo đảm xử lý và lưu dữ liệu khi hệ thống hạ nguồn có độ trễ hoặc lỗi. Nhóm tách bước tiếp nhận và xử lý thông qua SQS, bổ sung kiểm tra đầu vào, idempotency, retry và DLQ. Demo trình bày kết quả bốn tuần; mỗi bằng chứng được ghi rõ môi trường và ngày thực hiện.”

### 00:40–01:40 — Quân

“Client gửi POST tới API Gateway. Producer kiểm tra dữ liệu, sinh mã đơn rồi gửi SQS. API trả 202 sau khi gửi message thành công. SQS chuyển công việc sang Consumer thông qua Event Source Mapping; Consumer ghi bảng Orders với trạng thái PROCESSED. Vì xử lý bất đồng bộ, 202 chưa có nghĩa đơn đã hoàn tất. Nhóm phải tìm đúng orderId trong DynamoDB để xác nhận bước cuối. Khi Consumer thất bại, message được retry theo visibility timeout; vượt số lần nhận cấu hình thì chuyển DLQ. CloudWatch lưu log và metrics. Phần Alarm/SNS có bằng chứng riêng trên Lab Khôi, không mặc định giống Lab Quân.”

### 01:40–02:40 — Khôi

“Request có customerId, productId và quantity. Hai trường định danh phải là chuỗi không rỗng; quantity là số nguyên dương, không chấp nhận bool, float hoặc chuỗi số. Sau validation, Producer tạo orderId UUID, trạng thái PENDING và createdAt UTC. Nếu gửi SQS lỗi, API trả 500 thay vì báo đã tiếp nhận. Trong Tuần 4 nhóm phát hiện mã Producer trên Lab Quân cũ hơn source. Phiên nghiệm thu đã lưu ZIP rollback, triển khai đúng source của commit main và kiểm tra lại hash trước khi chạy test. Đây là ví dụ kiểm thử source tốt vẫn cần đối chiếu deployment thực tế.”

### 02:40–03:40 — Quân

“Đây là mapping đã xác minh đúng orders-queue tới order-consumer, ở trạng thái Enabled và batch size 1. Đơn nghiệm thu Tuần 4 có orderId e941e651-2be5-4a1e-9575-9bc47657967d. API trả 202, sau đó GetItem với ConsistentRead xác nhận PROCESSED. Mã đơn nối phản hồi API với item cuối, giúp tránh nhầm một bản ghi cũ với kết quả đang demo. Nếu quay một request mới, nhóm dùng mã đơn mới trả về để truy vấn, không sử dụng lại kết quả của request trước như thể vừa thực thi.”

### 03:40–04:45 — Khôi

“Ma trận nghiệm thu thực hiện 13 request: một hợp lệ và 12 invalid. Các ca sai gồm JSON lỗi cú pháp, root là array, thiếu từng trường, chuỗi whitespace và quantity bằng 0, âm, string, float hoặc bool. Tất cả ca invalid trả 400. Source đã đối chiếu cho thấy validation kết thúc trước send_message; unit tests kiểm tra nhánh này. Metrics toàn đợt ghi nhận đúng ba lần gửi vào queue: đơn hợp lệ, một replay và một sentinel lỗi. Nhóm không dùng chỉ riêng queue count xấp xỉ để kết luận tuyệt đối rằng không có message mới.”

### 04:45–06:00 — Quân

“Consumer ghi bằng điều kiện attribute_not_exists(orderId). Nếu đơn đã tồn tại, Consumer đọc nhất quán mạnh rồi so sánh các trường nghiệp vụ và createdAt. Phát lại nguyên payload qua SQS được xử lý thành công, item giữ nguyên. Direct test đổi quantity thành 99 với cùng mã đơn trả ORDER_CONFLICT và cũng không ghi đè. Để kiểm tra retry, nhóm chỉ gửi một sentinel invalid JSON mới. CloudWatch ghi năm lỗi đúng messageId, cách nhau khoảng 60 giây. Sau đó queue chính trống, DLQ tăng từ hai lên ba. Đây là bằng chứng tương quan của redrive; nhóm không nhận message DLQ để đọc body và không can thiệp hai message lịch sử.”

### 06:00–07:05 — Khôi

“Collector có sẵn trong repo thu metrics theo cửa sổ thời gian nghiệm thu. Producer có 13 invocation, không lỗi; Consumer có sáu lỗi dự kiến gồm một conflict và năm lần invalid JSON, không có throttling trong cửa sổ đo. Khi xem metric phải tách lỗi chủ động tạo khỏi sự cố ngoài dự kiến. Lab Quân hiện chưa có alarm và SNS của dự án. Các ảnh sau thuộc Lab Khôi ngày 24/10, thể hiện subscription confirmed, publish email và manual Alarm State dẫn tới email. Nhóm ghi rõ đó là phép thử đường phân phối cảnh báo, chưa phải bằng chứng DLQ metric tự kích hoạt email mới trong Tuần 4.”

### 07:05–08:10 — Quân

“Benchmark B1 ngày 24/10 dùng ba kịch bản, mỗi kịch bản 20 message. Cả Standard và FIFO đều gửi nhận đủ; Standard có sai thứ tự, FIFO giữ thứ tự trong từng group ở lần đo. Throughput khoảng hai đến ba message mỗi giây phản ánh client tuần tự và mạng của thí nghiệm, không phải giới hạn SQS. B2 có 10/10 HTTP 202 và 10/10 item PROCESSED. Thời gian 3,5846 giây là thời gian đợt đối soát sau gửi, không phải latency từng đơn. Ảnh B3 chứng minh hai record trong cùng RequestId Lambda, khác direct batch test. Mẫu nhỏ chưa đủ để suy ra năng lực production.”

### 08:10–09:00 — Quân

“Chi phí phụ thuộc API calls, số invocation và GB-seconds, thao tác message, đọc ghi DynamoDB, log, alarm và notification. Nhóm tránh thử lặp không cần thiết, tái dùng dữ liệu có provenance và chưa đổi memory hoặc batch khi chưa có so sánh đủ tin cậy. Conditional write và strong read được giữ vì tính đúng đắn. Queue chính, DLQ, Orders và log được giữ cho demo; hai queue benchmark rỗng được phân loại xem xét sau nghiệm thu. Không có purge hoặc xóa tài nguyên tự động, cũng không tuyên bố số tiền tiết kiệm khi chưa có hóa đơn đối soát.”

### 09:00–09:20 — Khôi và Quân

“Đề tài đã kiểm chứng luồng bất đồng bộ, validation, idempotency, conflict và retry trong phạm vi Learner Lab. Bộ hồi quy đạt 56 tests và 114 subtests. Hướng phát triển gồm authorization cho API, partial batch failure và kiểm thử tải có phương pháp rộng hơn. Nhóm chịu trách nhiệm về mã, kết quả và minh chứng, có khai báo phần AI hỗ trợ. Nhóm em xin cảm ơn thầy.”

## 3. Tài sản màn hình đã có

- [Báo cáo và sơ đồ](final-report.md), [ma trận và inventory Tuần 4](week4-report.md), [gate offline/CI](evidence/week4/offline-validation.md).
- Ảnh Console **lịch sử 24/10**: [B3 hai record](evidence/week3/quan/b3-2026-10-24/screenshots/W3-B3-CloudWatch-Two-Record-Batch.jpg), [Alarm History Khôi](evidence/week3/khoi/W3-CW-DLQ-Alarm-History.png), [SNS subscription](evidence/week3/khoi/W3-SNS-Topic-Subscription-Confirmed.png), [email cảnh báo](evidence/week3/khoi/W3-SNS-Alarm-Email-Received.png).
- Dữ liệu benchmark/load gốc và chỉ mục: [evidence Tuần 3](evidence/week3/README.md), [provenance Tuần 4](evidence/week4/README.md).

## 4. Checklist ghi hình

- Chuẩn bị sẵn đúng Lab/Region, source, báo cáo, bảng Orders tìm theo mã đơn và CloudWatch filter; không mở credential panel, account menu hoặc inbox ngoài email minh chứng đã cho phép.
- Giữ nguyên thông tin sinh viên/MSSV trên minh chứng theo yêu cầu học phần, cùng tên dịch vụ, resource và kết quả. Không chỉnh nội dung log, response hoặc trạng thái hiển thị; không mở credential hoặc secret key trong khung quay.
- Chọn một cách trình bày: thao tác live có mã đơn mới, hoặc dẫn lại kết quả đã ghi rõ ngày. Không nói “vừa chạy” khi đang chiếu ảnh cũ.
- Không chạy lại poison/retry, benchmark hoặc thay ESM chỉ để quay. Dùng năm mốc log và kết quả đã có để tránh thêm lỗi và message thừa.
- Đọc thử, bấm giờ từng đoạn; lời dẫn có thể rút theo tốc độ nói thực tế, giữ tổng dưới 10 phút. Cả hai thành viên xuất hiện và giải thích đúng phần việc.
- Kiểm tra âm thanh, chữ đọc được, MSSV thể hiện đúng và không có credential; xem lại video xuất cuối từ đầu tới cuối trước khi nộp. Chỉ ghi nhận video tồn tại sau khi thực sự quay và kiểm tra file.

Nếu phiên Lab hết hạn, dùng báo cáo và ảnh/JSON lịch sử kèm ngày/môi trường. Nếu quay live không thấy item ngay, đọc đúng orderId và kiểm tra mapping/log; không tạo request liên tục để “thử lại” mà không tìm nguyên nhân.
