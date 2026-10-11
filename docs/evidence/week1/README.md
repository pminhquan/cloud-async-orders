# Minh chứng Tuần 1

## 1. Lưu trữ và nộp minh chứng

26 ảnh PNG riêng tư tại `D:\PROJECT\cloud-project\private-evidence\week1` đã được kiểm tra ngày 2026-10-11, cùng kết quả AWS do SV1 cung cấp. Tài liệu ghi nhận các lần kiểm thử đã có, không chạy lại AWS tests.

Chưa kiểm tra rubric gốc để xác nhận yêu cầu hiển thị Account ID hoặc metadata cụ thể trong ảnh. Nộp theo hướng dẫn thực tế của giảng viên, giữ bản gốc ngoài repo/lịch sử Git và không bịa hoặc sửa kết quả minh chứng.

Account ID là mã định danh AWS, không phải thông tin xác thực; xuất hiện trong ảnh không tự động có nghĩa là lộ bí mật. Khi công khai, nên hạn chế thông tin cá nhân và mã định danh không cần thiết. Không đưa access key, secret key, session token, mật khẩu, cookie xác thực hoặc thông tin xác thực khác vào ảnh nộp hay ảnh công khai. Repo hiện chưa có ảnh công khai đã xử lý.

Thời gian chụp, người thực hiện và kênh nộp chưa được xác nhận; bổ sung theo hướng dẫn nộp minh chứng. Timestamp CloudWatch/thuộc tính file không thay thế thời gian chụp hoặc giờ làm.

| Ref | Nội dung | Nguồn / giới hạn |
| :--- | :--- | :--- |
| REF-01 | Console và Region `us-east-1` | Nhóm ảnh LAB bên dưới |
| REF-02 | `LabRole` tồn tại, trust có Lambda (IAM Global) | Nhóm LAB; không chứng minh đầy đủ quyền |
| REF-03 | Tags `Project=AsyncOrderProcessing`, `Owner=Khoi-Quan` tại `us-east-1` theo thông tin SV1 | Chưa có ảnh Tags |

## 2. Kết quả Consumer PoC

### W1-Q-CONFIG

[Cấu hình đầy đủ](../../aws-inventory.md): SQS Standard/SSE-SQS; `maxReceiveCount=3`, DLQ retention 14 ngày; Python 3.13, timeout 10 giây, memory 128 MB; trigger Enabled, batch 1/window 0 giây, maximum concurrency 2, partial batch failures Disabled. Ảnh thuộc nhóm SQS-CONFIG, LAMBDA và TRIGGER.

Visibility timeout 60 giây, execution role `LabRole` và tags theo thông tin SV1; chưa có ảnh mở chi tiết visibility/role association/Tags. Theo báo cáo SV1, Lab hạn chế kiểm tra policy; invocation và log thành công không xác nhận toàn bộ quyền hoặc quyền cross-account.

### W1-Q-DIRECT

| Test Lambda trực tiếp | Kết quả | Nhóm ảnh |
| :--- | :--- | :--- |
| Event hợp lệ | `Succeeded`, `POC_VALIDATED`, processedCount 1 | DIRECT |
| Quantity sai | `ConsumerError: INVALID_SCHEMA` — kết quả âm mong đợi | DIRECT |

Tên event được lưu và tên Execution Results trong ảnh valid khác nhau; chỉ xác nhận success/log nhìn thấy. Test trực tiếp không chứng minh SQS retry/DLQ.

### W1-Q-E2E

| Test qua SQS | Kết quả | Nhóm ảnh |
| :--- | :--- | :--- |
| `ORD-W1-Q-003`, quantity 2 | Gửi thành công; CloudWatch `/aws/lambda/order-processor` có `POC_VALIDATED` đúng orderId, sự kiện UTC `2026-10-11T05:48:42.106Z` | SQS-VALID |
| `ORD-W1-Q-ERR-002`, quantity 0 | `INVALID_SCHEMA` lặp; có body cùng orderId/quantity trong `orders-dlq`; SV1 xác nhận chuỗi retry → DLQ | SQS-INVALID |

Ảnh retry chưa mở đủ `messageId` để đối soát độc lập từng lần nhận; cần log mở rộng đã che dữ liệu nếu phải chứng minh toàn chuỗi. `maxReceiveCount=3` không cam kết đúng 3 invocation; receive count ở DLQ không thay cho số lần xử lý tại queue nguồn.

PoC kiểm tra `orderId`, `items[].sku` và `quantity` là số nguyên dương, ghi log và ném exception khi lỗi. Chưa ghi DynamoDB hoặc xử lý lặp an toàn cho nghiệp vụ; batch lỗi áp dụng cả lô. ESM có thể xóa tin sau success mà chưa lưu nghiệp vụ, nên chỉ dùng dữ liệu synthetic. Các ảnh thủ công `ORD-W1-Q-001` dùng `productId`, không có `sku`; chúng không chứng minh Consumer chấp nhận schema đó hoặc tự xóa `ORD-W1-Q-003`.

Source `src/consumer/lambda_function.py` được đọc riêng ở worktree `codex/sv1-sqs-consumer-poc`, không có trên nhánh docs; chưa đối soát byte-for-byte với deployed artifact.

## 3. Chỉ mục 26 ảnh riêng tư

Các filename dưới đây tham chiếu thư mục ở mục 1, không phải ảnh/link công khai. Nhóm ảnh được dùng để tra lại các kết quả ở mục 2.

| Nhóm | Filename | Nội dung / giới hạn |
| :--- | :--- | :--- |
| LAB (3) | `week1-aws-console-initial.png`, `week1-iam-labrole-summary.png`, `week1-iam-labrole-trust.png` | Console/Region, role/trust và một phần policy; số chi phí trên ảnh không thay báo cáo chi phí cuối kỳ |
| SQS-CONFIG (4) | `week1-sqs-main-created.png`, `week1-sqs-dlq-created.png`, `week1-sqs-dlq-config.png`, `week1-sqs-dlq-linked.png` | Queue/DLQ Standard, SSE-SQS, redrive 3; hai ảnh liên kết không phải hai test độc lập |
| SQS-MANUAL (4) | `week1-sqs-send-success.png`, `week1-sqs-receive-success.png`, `week1-sqs-message-body.png`, `week1-sqs-message-deleted.png` | Send/receive/delete thủ công; body dùng productId |
| LAMBDA (3) | `week1-lambda-order-processor-created.png`, `week1-lambda-config-10s.png`, `week1-lambda-consumer-deployed.png` | Tạo function (ban đầu còn code mặc định), cấu hình và cập nhật source PoC |
| DIRECT (4) | `week1-lambda-valid-test-success.png`, `week1-lambda-valid-execution-logs.png`, `week1-lambda-invalid-test-error.png`, `week1-lambda-invalid-execution-logs.png` | Test trực tiếp valid/invalid; orderId valid trực tiếp khác test qua SQS |
| TRIGGER (2) | `week1-sqs-trigger-disabled.png`, `week1-sqs-trigger-enabled.png` | Disabled là bước trước; Enabled có batch 1/window None, concurrency 2, partial failures No |
| SQS-VALID (2) | `week1-sqs-lambda-message-sent.png`, `week1-sqs-lambda-consumer-success.png` | ORD-W1-Q-003 gửi với sku; log thành công và INIT_START Python 3.13 |
| SQS-INVALID (4) | `week1-sqs-invalid-message-sent.png`, `week1-sqs-lambda-retry-error-logs.png`, `week1-sqs-dlq-message-arrived.png`, `week1-sqs-dlq-message-body.png` | ORD-W1-Q-ERR-002, lỗi lặp, DLQ có tin/body; retention 14 ngày |

## 4. Bàn giao còn cần xác nhận

[Sơ đồ Mermaid](../../architecture/README.md) đã có, chờ sinh viên rà soát/nộp. Còn thiếu ảnh Tags, xác nhận mô hình/quyền tích hợp tài khoản, biên bản họp nhóm và thông tin nộp minh chứng theo hướng dẫn giảng viên. [Nhật ký](../../worklog/week1.md) chưa có giờ thực tế xác nhận. Diff tài liệu hiện chưa commit, cần sinh viên duyệt trước khi lưu/nộp.
