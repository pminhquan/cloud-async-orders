# Kế hoạch Tuần 1

Mục tiêu: hoàn thành nghiên cứu AWS, tài liệu nền tảng, sơ đồ kiến trúc, kiểm tra môi trường Lab và ghi nhận giờ làm/minh chứng theo [yêu cầu dự án](requirements.md).

## 1. Nhiệm vụ và trạng thái

| Mã | Nhiệm vụ / bàn giao | Phụ trách | Trạng thái và minh chứng |
| :--- | :--- | :--- | :--- |
| **W1-T01** | README, yêu cầu, phân công, hợp đồng và danh mục AWS | Khôi tổng hợp; Quan cung cấp phần SV1 | Hoàn thành tài liệu nền tảng; đã có trong `main` sau ba PR Tuần 1. |
| **W1-T02a** | Nghiên cứu SQS Standard/FIFO và DLQ | Quan | Hoàn thành [nghiên cứu SV1](research/standard-vs-fifo.md), có kết quả PoC. |
| **W1-T02b** | Nghiên cứu API Gateway, DynamoDB, SNS, retry/alerting | Khôi | Hoàn thành [nghiên cứu SV2](research/sv2-services.md); xem thêm [báo cáo PoC SV2](sv2-week1.md). |
| **W1-T03** | Sơ đồ đủ thành phần, luồng chính/lỗi và trách nhiệm | Quan; Khôi góp ý SV2 | Hoàn thành [sơ đồ Mermaid](architecture/README.md); việc nộp còn chờ xác nhận. |
| **W1-T04** | Kiểm tra Lab, Region, `LabRole` và tương thích tài khoản | Cả hai | [Minh chứng PoC](evidence/week1/README.md): `us-east-1`, role tồn tại và invocation thành công; quyền đầy đủ/mô hình tích hợp tài khoản còn chờ xác nhận. |
| **W1-T05** | Quy ước và kiểm tra tags | Cả hai | `Project=AsyncOrderProcessing`, `Owner=Khoi-Quan` theo báo cáo SV1; SV2 tự báo cáo **80%** trong [báo cáo SV2](sv2-week1.md), chưa có ảnh xác minh. Chưa xác nhận đầy đủ tags; nhóm không yêu cầu thêm ảnh Tags SV2 cho Tuần 1. |
| **W1-T06** | Hoạt động, giờ làm và minh chứng (≥ 8 giờ/người) | Mỗi người cung cấp; Khôi tổng hợp riêng | [Nhật ký](worklog/week1.md) ghi hoạt động hai thành viên; nhóm khai báo cả hai đã đạt ≥ 8 giờ. Chưa có tổng giờ chính xác, ngày/giờ hoặc phân bổ chi tiết; chưa xác minh độc lập. |
| **W1-T07** | Khai báo AI theo yêu cầu giảng viên | Khôi tổng hợp/nộp riêng; Quan xác nhận phần mình | Theo thông tin nhóm, đã chuẩn bị riêng; nội dung chưa được kiểm tra tại repo. Việc nộp vẫn chờ xác nhận. |
| **W1-T08** | Mã nguồn PoC và minh chứng kỹ thuật | Quan: Consumer/SQS/DLQ; Khôi: Producer/API/DynamoDB/SNS | Hoàn thành hai PoC riêng, có cả hai mã Lambda, 8 Consumer unit tests và [32 ảnh](evidence/week1/README.md). Chưa tích hợp E2E. |
| **W1-T09** | Nộp báo cáo tiến độ và bộ bàn giao Tuần 1 | Khôi tổng hợp; cả hai cung cấp phần mình | Chờ xác nhận nộp báo cáo tuần, sơ đồ, minh chứng và thông tin hành chính theo hướng dẫn giảng viên. |

## 2. Ràng buộc và phạm vi

Chỉ dùng role/profile Lab cho phép (`LabRole`/`LabInstanceProfile`), không tạo IAM user/role mới; tổng Lambda concurrency toàn tài khoản ≤ 10. Chỉ gắn/kiểm tra tags trên tài nguyên được phép tạo, không tạo tài nguyên rác để chụp ảnh.

Consumer PoC đã xác nhận validate/log và retry/DLQ; Producer/API PoC trả `202`. Xem [cấu hình](aws-inventory.md) và [minh chứng](evidence/week1/README.md). Không suy ra giảng viên đã duyệt prototype sớm nếu chưa có xác nhận. Tích hợp Producer → SQS → Consumer → DynamoDB thuộc Tuần 2; idempotency và cảnh báo tích hợp chưa triển khai. CloudWatch Alarm vẫn là kế hoạch.

Phần kỹ thuật Tuần 1 đã có trong repo. Khai báo giờ làm chưa thay thế bảng giờ chi tiết; báo cáo tuần và khai báo AI vẫn chờ xác nhận nộp. Không coi việc merge PR là hoàn tất nộp bài.
