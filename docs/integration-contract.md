# Hợp Đồng Tích Hợp Dữ Liệu & Quy Tắc Xử Lý (Integration Contract)

Tài liệu đặc tả hợp đồng dữ liệu, cơ chế idempotency (xử lý lặp an toàn) và cấu hình Event Source Mapping cho hệ thống **cloud-async-orders**.

> [!NOTE]
> **Hợp đồng đích cho hệ thống hoàn chỉnh bên dưới vẫn là ĐỀ XUẤT (PROPOSED).** PoC Tuần 1 đã kiểm thử schema `orderId` / `items[].sku` / positive integer `quantity` trên SQS Standard. Cấu hình thực tế: batch 1, window 0 giây, maximum concurrency 2, Report batch item failures **Disabled**; lỗi ném exception làm thất bại cả batch. Chưa có ghi DynamoDB/production-grade idempotency hoặc partial batch response. Nguồn và kết quả xem [inventory](aws-inventory.md) và [evidence](evidence/week1/README.md); không coi các bước thiết kế bên dưới là đã cài đặt.

## 1. Cấu Trúc JSON Đơn Hàng Đề Xuất (Proposed JSON Schema)

Dữ liệu JSON đơn giản hóa, chỉ bao gồm `orderId` và danh sách `items` chứa `sku` và `quantity` (số nguyên dương $\ge 1$):

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

- `orderId` (String, bắt buộc, không rỗng): Mã định danh đơn hàng duy nhất; client bắt buộc tái sử dụng cùng `orderId` khi gửi retry yêu cầu.
- `items` (Array, bắt buộc): Mảng không rỗng (`items.length >= 1`).
- `items[].sku` (String, bắt buộc, không rỗng): Mã sản phẩm dạng chuỗi ký tự.
- `items[].quantity` (Integer, bắt buộc): Số lượng đặt mua, phải là số nguyên dương $\ge 1$.

## 2. Giao Tiếp Giữa Các Tầng (Interfaces & Responsibilities)

- **Client -> API Gateway -> Producer Lambda**:
  - Endpoint: `POST /orders`.
  - Producer validate cú pháp và schema cơ bản.
  - **Chỉ trả về `202 Accepted` sau khi `SendMessage` vào SQS thành công**. Trả về `400 Bad Request` nếu input sai; trả về `5xx` nếu gửi SQS thất bại.
- **Producer Lambda -> Amazon SQS**:
  - Gửi payload đơn hàng vào `MessageBody` của hàng đợi SQS.
  - *Giao diện FIFO*: Nếu sử dụng hàng đợi FIFO, lệnh gửi bắt buộc phải cung cấp `MessageGroupId` và `MessageDeduplicationId` (hoặc bật Content-Based Deduplication trên hàng đợi); phương án ánh xạ các tham số này ở trạng thái ĐỀ XUẤT (PROPOSED / chưa chốt), không gửi tin nhắn FIFO khi thiếu các tham số bắt buộc.
- **Amazon SQS -> Consumer Lambda**:
  - Lambda thăm dò hàng đợi SQS qua Event Source Mapping (ESM) và gọi Consumer để xử lý từng lô.
  - Lambda ESM tự động xóa các tin nhắn xử lý thành công khỏi SQS. Theo thiết kế đích, bật `ReportBatchItemFailures` trên ESM và để handler trả về `batchItemFailures` chứa các tin nhắn thất bại. PoC hiện chưa bật tính năng này.
- **Consumer Lambda -> Amazon DynamoDB**:
  - Consumer validate nội dung body và thực hiện ghi nguyên tử có điều kiện (conditional `PutItem` với khóa `orderId`).

## 3. Cơ Chế Xử Lý Trùng Lặp & Idempotency (Xử Lý Lặp An Toàn)

1. **Ghi có điều kiện**: Consumer thực hiện `PutItem` với điều kiện `attribute_not_exists(orderId)`.
2. **Xử lý khi xảy ra xung đột điều kiện (`ConditionalCheckFailedException`)**:
   - Consumer thực hiện đọc nhất quán (Consistent Read) bản ghi hiện có từ DynamoDB để so sánh các trường nghiệp vụ ổn định (`items` gồm `sku` và `quantity`), loại trừ các trường trạng thái/metadata xử lý nếu có.
   - **Payload trùng khớp (Identical payload)**: Coi là xử lý lặp an toàn (idempotent success), không ghi đè dữ liệu; ESM sẽ xóa tin nhắn khỏi hàng đợi.
   - **Payload xung đột (Conflicting payload - cùng `orderId` nhưng khác `items`)**: Giữ nguyên bản ghi cũ trong DynamoDB; trả về failure cho tin nhắn này để SQS retry theo cơ chế thông thường và chuyển sang DLQ sau khi vượt ngưỡng nhận (`maxReceiveCount`). Tuyệt đối không tự ý chuyển thẳng sang DLQ từ mã nguồn.
3. **Nguyên tắc ghi log an toàn**: Tuyệt đối không log toàn bộ payload cũ/mới hay thông tin nhạy cảm; chỉ log tối thiểu mã `orderId` và mã lỗi để đối soát. Không tự ý khẳng định các bước chuyển trạng thái DB khi chưa cài đặt.

## 4. Cấu Hình Event Source Mapping & Giới Hạn (PROPOSED)

*Tham khảo tài liệu AWS chính thức*:
- [Configure SQS with Lambda](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)
- [Lambda SQS Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)

- **Visibility Timeout**: AWS khuyến nghị Visibility Timeout của SQS $\ge 6 \times \text{Function Timeout} + \text{Standard Batching Window}$. PoC dùng visibility timeout 60 giây, function timeout 10 giây và batch window 0 giây, đáp ứng khuyến nghị này. Batching window chỉ áp dụng cho Standard queue; FIFO batch tối đa 10. Cấu hình cho giai đoạn tích hợp cần được kiểm tra lại theo thời gian xử lý thực tế.
- **Giới hạn Concurrency**: Tổng concurrency toàn tài khoản AWS Learner Lab $\le 10$ (tính chung cho producer, consumer và các hàm khác). PoC đã đặt `MaximumConcurrency` là 2 trên Event Source Mapping; cần đối soát phân bổ khi tích hợp Producer. Khả năng cấp phát Reserved Concurrency vẫn CHƯA RÕ (UNKNOWN) do quota tài khoản Lab hạn chế.
- **Xử lý lỗi theo lô (Error Handling)**:
  - Nếu hàm Lambda ném ra Exception chưa bắt, toàn bộ lô tin nhắn sẽ bị coi là thất bại và thử lại.
  - Cấu hình `ReportBatchItemFailures` để chỉ retry các tin nhắn bị lỗi; đối với FIFO queue, handler phải dừng xử lý ở tin nhắn lỗi đầu tiên và trả về ID của tin nhắn lỗi cùng các tin nhắn chưa xử lý trong lô để bảo toàn thứ tự nghiêm ngặt.
