# Kiểm thử tải có kiểm soát & Đối soát E2E DynamoDB (W3-03)

## 1. Mục tiêu và nguyên tắc thiết kế

Công cụ [`scripts/load_test_orders.py`](../scripts/load_test_orders.py) thay thế cách gọi API hard-code cũ bằng một công cụ kiểm thử tải có cấu hình, giới hạn tốc độ an toàn và tự động đối soát trạng thái xử lý cuối cùng trong DynamoDB `Orders`.

### Các nguyên tắc cốt lõi

1. **Không phụ thuộc endpoint hard-code:** Người dùng bắt buộc truyền `--endpoint https://<api-id>.execute-api.us-east-1.amazonaws.com/orders` (Và script PowerShell `scripts/test-order-api.ps1` cũng đã được cập nhật nhận `-EndpointUrl` / `$env:ORDER_API_URL` kèm cờ `-Execute`).
2. **Tôn trọng giới hạn Concurrency `<= 10` của AWS Learner Lab:**
   - Giới hạn cứng `--rate <= 10.0` requests/giây và `--count <= 100` requests/lần chạy (mặc định an toàn: `--count 10 --rate 2.0`).
   - Không tự ý nâng Lambda reserved/account concurrency và không chạy stress test vô hạn.
3. **Phân biệt rạch ròi `HTTP 202` và `DynamoDB PROCESSED`:**
   - `HTTP 202 Accepted` = `order-producer` đã nhận request hợp lệ và thực hiện `sqs.send_message()` thành công vào `orders-queue`.
   - `DynamoDB status = PROCESSED` = `order-consumer` đã đọc message từ SQS, kiểm tra schema/idempotency và ghi thành công vào bảng `Orders`.
   - Công cụ **không bao giờ** coi `HTTP 202` đồng nghĩa với việc đơn hàng đã được xử lý xong ở Consumer.
4. **Đối soát DynamoDB an toàn (`GetItem` only):**
   - Với mỗi `orderId` thu được từ phản hồi `HTTP 202`, script thực hiện `table.get_item(Key={"orderId": order_id}, ConsistentRead=True)` theo vòng lặp polling có giới hạn (`--reconcile-timeout`, `--reconcile-max-polls`) và exponential backoff nhẹ.
   - **Không dùng `Scan`** toàn bảng và **chỉ đọc dữ liệu (read-only)**, không sửa/xóa bất kỳ item nào trong bảng `Orders`.
   - Nếu thiếu quyền đọc DynamoDB (`AccessDeniedException`), script báo cáo đúng trạng thái `UNVERIFIED_DYNAMODB_ACCESS_ERROR` thay vì báo sai kết quả.

---

## 2. Cấu trúc dữ liệu đầu ra

Khi chạy với `--output-dir`, công cụ xuất hai file:

1. **`load-test-summary.json`**:
   - `configuration`: thông số endpoint host, `requestCount`, `rateLimitPerSec`, `timeoutSeconds`, `customerPrefix`, `tableName`.
   - `summary`:
     - `requestsAttempted`
     - `http202AcceptedCount`
     - `http400Count`, `http429Count`, `http5xxCount`, `timeoutCount`, `otherErrorCount`
     - `orderIdsCollectedCount`, `missingOrderIdOn202Count`, `malformed202ResponseCount`
     - `apiLatencyMs` (`minMs`, `maxMs`, `meanMs`, `medianMs`, `p95Ms`)
   - `reconciliation`:
     - `verificationStatus` (`ALL_PROCESSED`, `PARTIALLY_PROCESSED`, `NONE_PROCESSED_WITHIN_TIMEOUT`, `UNVERIFIED`, `UNVERIFIED_DYNAMODB_ACCESS_ERROR`, `DRY_RUN_NOT_EXECUTED`)
     - `orderIdsRequested`, `processedCount`, `pendingOrOtherStatusCount` (đã đọc được item nhưng `status != PROCESSED`), `notFoundCount` (item chưa xuất hiện `NOT_FOUND_YET`), `unverifiedCount` (chưa kiểm tra được do hết ngân sách, lỗi truy vấn hoặc `AccessDeniedException`); bốn nhóm này phân hoạch đầy đủ `orderIdsRequested` và được `scripts/generate_week3_report.py` hiển thị chi tiết cùng tổng `Remaining`
     - `reconciliationDurationSeconds`, `pollsExecuted`
2. **`load-test-results.csv`**:
   - Ghi nhận chi tiết từng request: `runId`, `requestId`, `timestampUtc`, `httpStatus`, `responseTimeMs`, `orderId`, `errorCategory`, `reconciledState`.

---

## 3. Lệnh sử dụng

### 3.1. Chế độ Dry-run Offline (Mặc định)

```bash
python scripts/load_test_orders.py \
  --endpoint https://example-api.execute-api.us-east-1.amazonaws.com/orders \
  --count 10 \
  --rate 2.0 \
  --dry-run \
  --output-dir artifacts/load-dryrun
```

### 3.2. Chế độ Thực thi có Kiểm soát trên AWS Learner Lab

```bash
python scripts/load_test_orders.py \
  --endpoint https://<api-id>.execute-api.us-east-1.amazonaws.com/orders \
  --count 20 \
  --rate 2.0 \
  --timeout 5.0 \
  --customer-prefix CUS-LOAD-W3 \
  --table-name Orders \
  --reconcile-timeout 25 \
  --reconcile-max-polls 6 \
  --execute \
  --confirm-target <api-id>.execute-api.us-east-1.amazonaws.com \
  --output-dir artifacts/load-live
```

---

## Giới hạn polling DynamoDB

Reconciliation kiểm tra hạn trước từng GetItem, kể cả giữa các orderId trong một lượt. Sau khi hết ngân sách không bắt đầu query hoặc backoff mới. SDK dùng một tổng lần thử cho mỗi call và connect/read timeout hữu hạn; request đã bắt đầu chịu timeout của call đó.

Công cụ gửi tải tuần tự và không thay cấu hình Lambda. Giới hạn rate ở client không tự bảo đảm tổng concurrency tài khoản; runbook hướng dẫn kiểm tra cấu hình vận hành trước khi chạy.
