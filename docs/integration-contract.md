# Hợp Đồng Tích Hợp Dữ Liệu & Quy Tắc Xử Lý (Integration Contract)

Tài liệu đặc tả hợp đồng dữ liệu, cơ chế idempotency (xử lý lặp an toàn) và cấu hình Event Source Mapping cho hệ thống **cloud-async-orders**, phân biệt PoC Tuần 1 với tích hợp Tuần 2.

> [!NOTE]
> **Schema phẳng ở mục 1.2 là hợp đồng Tuần 2 đã được nhóm thống nhất.** Mã Consumer của Quan mới hoàn thành local, chưa merge vào `main` hoặc triển khai AWS. Cấu hình và các ca AWS do Khôi báo cáo chưa được xác minh độc lập trong lượt cập nhật này; full E2E chưa được xác minh. Phân công và tiến độ xem [kế hoạch Tuần 2](week2-plan.md), giờ làm xem [nhật ký](worklog/week2.md).

## 1. Hợp đồng dữ liệu theo từng giai đoạn

### 1.1. Định dạng PoC Tuần 1 — giữ làm lịch sử

PoC Tuần 1 dùng `orderId` và danh sách `items` chứa `sku`, `quantity`:

```json
{
  "orderId": "example-order-001",
  "items": [
    {
      "sku": "example-sku-001",
      "quantity": 1
    }
  ]
}
```

- `orderId` (String, bắt buộc, không rỗng): Mã đơn hàng dùng cho PoC.
- `items` (Array, bắt buộc): Mảng không rỗng (`items.length >= 1`).
- `items[].sku` (String, bắt buộc, không rỗng): Mã sản phẩm dạng chuỗi ký tự.
- `items[].quantity` (Integer, bắt buộc): Số lượng đặt mua, phải là số nguyên dương $\ge 1$.

Consumer Tuần 1 kiểm tra dữ liệu, log `POC_VALIDATED` và ném exception khi có lỗi; chưa ghi DynamoDB, chưa có idempotency lưu trữ hoặc partial-batch response. Cấu hình đã ghi nhận: Consumer `order-processor`, SQS Standard, batch 1, window 0 giây, maximum concurrency 2, `ReportBatchItemFailures` Disabled, `maxReceiveCount=3`, visibility timeout 60 giây và Lambda timeout 10 giây. Nguồn: [inventory Tuần 1](aws-inventory.md), [minh chứng Tuần 1](evidence/week1/README.md). Minh chứng retry thiếu đủ `messageId` để đếm độc lập từng lần xử lý. Các ca SQS → Consumer/DLQ này không chứng minh E2E từ API tới DynamoDB.

### 1.2. Schema phẳng Tuần 2 — hợp đồng tích hợp chính thức của nhóm

```json
{
  "orderId": "ORD-W2-001",
  "customerId": "CUS001",
  "productId": "P001",
  "quantity": 2,
  "status": "PENDING",
  "createdAt": "2026-10-14T00:00:00+00:00"
}
```

- Producer sinh `orderId` và `createdAt`, đặt `status=PENDING`, rồi gửi JSON vào SQS. Consumer ghi item với `status=PROCESSED`, giữ `orderId`, `createdAt` và các trường nghiệp vụ.
- Root phải là JSON object. Các trường `orderId`, `customerId`, `productId`, `status`, `createdAt` bắt buộc là chuỗi không rỗng/không chỉ có khoảng trắng.
- `quantity` bắt buộc là số nguyên dương. Consumer local dùng kiểm tra kiểu nguyên chính xác, từ chối `bool`, số thực kể cả `2.0`, chuỗi số như `"2"`, giá trị `0`, số âm và trường bị thiếu. Không ép kiểu các giá trị sai thành số nguyên.
- Định dạng `items[].sku` chỉ thuộc PoC Tuần 1, không dùng thay schema phẳng Tuần 2. Ví dụ thời gian ở trên là dữ liệu minh họa, không phải ngày hoặc thời lượng làm việc.

## 2. Giao Tiếp Giữa Các Tầng (Interfaces & Responsibilities)

- **Client -> API Gateway -> Producer Lambda**:
  - Endpoint: `POST /orders`.
  - Client cung cấp dữ liệu nghiệp vụ `customerId`, `productId`, `quantity`; Producer chịu trách nhiệm kiểm tra đầu vào và tạo các trường còn lại theo mục 1.2.
  - Giao diện tích hợp yêu cầu **chỉ trả `202 Accepted` sau khi `SendMessage` vào SQS thành công**, trả `400 Bad Request` nếu input sai và `5xx` nếu gửi SQS thất bại. `202` xác nhận tiếp nhận vào queue, chưa xác nhận Consumer hoặc DynamoDB đã xử lý.
  - Producer trên `main` local tại `942a709` vẫn là PoC Tuần 1, tạo UUID và trả `202` mà chưa gọi SQS. Bản Producer gửi SQS trên AWS là thông tin Khôi báo cáo; cần bàn giao mã và minh chứng để đối chiếu, không coi yêu cầu phản hồi lỗi trên là đã được kiểm chứng đầy đủ.
- **Producer Lambda -> Amazon SQS**:
  - Dùng `QUEUE_URL`, gửi JSON schema phẳng vào `MessageBody` của SQS Standard `orders-queue`. Cấu hình `QUEUE_URL` và ca Producer → SQS thành công hiện là thông tin Khôi báo cáo.
  - Producer hiện sinh UUID mới cho mỗi request; HTTP retry có thể tạo `orderId` mới. Chưa có cơ chế bảo đảm deduplicate các yêu cầu HTTP lặp. Idempotency ở Consumer chỉ bảo vệ các lần nhận lại cùng `orderId` và trường nghiệp vụ ổn định.
- **Amazon SQS -> Consumer Lambda**:
  - Lambda thăm dò hàng đợi SQS qua Event Source Mapping (ESM) và gọi Consumer để xử lý từng lô.
  - Consumer đọc từng `Records[].body`, parse JSON và validate theo mục 1.2. Mã local Tuần 2 của Quan giữ **full-batch failure**: bất kỳ record lỗi nào cũng làm handler ném exception, không trả `batchItemFailures` hoặc báo thành công một phần.
  - Khi toàn bộ batch thành công, ESM xử lý việc xóa tin nhắn. Khi batch thất bại, tin nhắn được retry theo cấu hình queue/ESM; những record đã ghi trước lỗi có thể được nhận lại và phải deduplicate an toàn.
- **Consumer Lambda -> Amazon DynamoDB**:
  - Dùng boto3 và biến `TABLE_NAME`; môi trường tích hợp được báo cáo là `Orders`, partition key `orderId` kiểu String. Ghi `PROCESSED` bằng conditional `PutItem` theo mục 3.
  - Thiếu cấu hình, dữ liệu sai hoặc lỗi DynamoDB phải làm xử lý thất bại; không được nuốt lỗi DB để báo thành công. Khôi phụ trách triển khai, Quan cung cấp mã và kiểm tra hành vi Consumer.

## 3. Cơ Chế Xử Lý Trùng Lặp & Idempotency (Xử Lý Lặp An Toàn)

1. **Ghi có điều kiện**: Consumer thực hiện `PutItem` với điều kiện `attribute_not_exists(orderId)`.
2. **Xử lý khi xảy ra xung đột điều kiện (`ConditionalCheckFailedException`)**:
   - Chỉ lỗi điều kiện này dẫn tới `GetItem(Key={"orderId": orderId}, ConsistentRead=True)`. So sánh bốn trường ổn định: `customerId`, `productId`, `quantity`, `createdAt`; `orderId` là khóa định danh.
   - **Trùng khớp (Identical duplicate)**: Cùng khóa và cả bốn trường khớp thì coi là idempotent success, không ghi đè item. Không so sánh `status`, vì tin nhắn là `PENDING` còn item đã là `PROCESSED`. Việc xóa tin nhắn vẫn phụ thuộc kết quả toàn batch.
   - **Xung đột (Conflicting duplicate)**: Cùng `orderId` nhưng một trường ổn định khác thì giữ nguyên item gốc, báo `ORDER_CONFLICT` và ném lỗi để thất bại toàn batch.
   - Nếu đọc lại không có item, hoặc ghi/đọc gặp lỗi khác, handler phải báo thất bại và truyền lỗi; không coi là duplicate thành công.
3. **Retry và DLQ**: SQS redrive chuyển tin nhắn lỗi sang `orders-dlq` theo `maxReceiveCount`. Consumer không tự gửi thẳng vào DLQ. Ngưỡng receive count không chứng minh có đúng từng đó Lambda invocation, nhất là khi xử lý theo batch.
4. **Log an toàn**: Chỉ ghi mã lỗi cố định và các định danh `orderId`/`messageId` đã làm sạch, giới hạn độ dài theo từng nhánh xử lý. Không log toàn bộ payload, item cũ/mới, dữ liệu khách hàng/sản phẩm hoặc thông tin nhạy cảm.

Cơ chế trên đã có trong Consumer local tại [commit 0192d2b](https://github.com/pminhquan/cloud-async-orders/commit/0192d2b554cf9795e21eb1b0b20dba8c4102c243), cùng 15 unit tests đã qua theo kết quả local được bàn giao. Theo thông tin Quan, [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5) đang mở, chưa merge; mã chưa triển khai AWS. Ca SQS → Consumer → DynamoDB do Khôi báo cáo không chứng minh bản đang triển khai có conditional write hoặc idempotency này.

## 4. Cấu hình và giới hạn theo từng môi trường

### 4.1. Lab tích hợp Tuần 2 — Khôi tự báo cáo

Nhóm thống nhất dùng Lab của Khôi tại `us-east-1`; Khôi thực hiện triển khai. **Toàn bộ cấu hình dưới đây là thông tin Khôi báo cáo, chưa được kiểm tra trực tiếp trên AWS trong lượt cập nhật này.**

| Thành phần | Tên / cấu hình được báo cáo |
| :--- | :--- |
| API Gateway | `order-api`, `POST /orders` |
| Producer Lambda | `order-producer`, đã cấu hình `QUEUE_URL` |
| SQS Standard | `orders-queue` |
| DLQ / redrive | `orders-dlq`, `maxReceiveCount=5` |
| Consumer Lambda | `order-consumer`, `TABLE_NAME=Orders` |
| Consumer SQS trigger | Enabled, batch size 5, maximum concurrency 5 |
| DynamoDB | `Orders`, partition key `orderId` |
| SNS | `order-dlq-alert`; chưa có minh chứng CloudWatch Alarm → SNS hoạt động |

Chưa xác nhận cờ `ReportBatchItemFailures`/`FunctionResponseTypes`, visibility timeout, Lambda timeout, batching window, reserved concurrency và quyền hiệu lực `SendMessage`/`PutItem`/`GetItem` trên môi trường Tuần 2. Không chép cấu hình Tuần 1 sang Tuần 2 rồi coi là đã xác minh. Giới hạn tổng Lambda concurrency ≤ 10 là ràng buộc đã ghi trong [yêu cầu Lab](requirements.md); cần đối soát phân bổ và quota thực tế trước khi chạy tải.

### 4.2. Full-batch hiện tại và partial-batch dự kiến

PoC Tuần 1 đã ghi nhận partial-batch Disabled. Consumer local Tuần 2 của Quan hiện cũng ném lỗi để thất bại toàn batch. Partial-batch trong [yêu cầu hệ thống](requirements.md) vẫn là hướng dự kiến; chỉ dùng khi nhóm thống nhất thay đổi handler, cấu hình ESM bật `ReportBatchItemFailures` và kiểm thử đúng cặp mã/cấu hình. Không suy ra cờ này đã bật hoặc disabled trên Lab Tuần 2 từ thông tin batch size 5.

*Tham khảo tài liệu AWS chính thức*:

- [Configure SQS with Lambda](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)
- [Lambda SQS Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)

Giữ nguyên tham chiếu thiết kế visibility timeout ≥ 6 × Lambda timeout + batching window. Cấu hình PoC Tuần 1 là 60/10/0 giây; cấu hình tích hợp phải được kiểm tra lại theo thời gian xử lý thực tế. FIFO benchmarking, IaC, CloudWatch Alarm/SNS integration và báo cáo chi phí cuối kỳ không thuộc phần cốt lõi Tuần 2, trừ khi giảng viên yêu cầu.

## 5. Minh chứng E2E và các xác nhận còn thiếu

Khôi báo cáo hai luồng kiểm thử riêng thành công: Producer → SQS và SQS → Consumer → DynamoDB. **Full E2E chưa được xác minh.** `orderId=3435e200-ccd1-4664-90a8-633553d55188` do Producer tạo chưa có minh chứng đối chiếu trong log Consumer hoặc DynamoDB; không kết luận đơn đã được lưu, cũng không kết luận đơn bị mất.

Cần bàn giao đúng mã Producer/Consumer đang triển khai và đối chiếu cùng `orderId` qua phản hồi API, SQS, log Consumer, item DynamoDB `PROCESSED`. Sau khi tích hợp bản Consumer được chấp thuận, tiếp tục kiểm tra duplicate/conflict, lỗi DB, retry/DLQ, batch có lỗi và tải nhỏ có giới hạn; kết quả phải có minh chứng thực tế theo [W2-04–W2-10](week2-plan.md). Không dùng các ca Tuần 1 hoặc unit tests local để thay bằng chứng AWS Tuần 2.
