# Kết quả triển khai offline Tuần 3

Dự án `cloud-async-orders`. Bản triển khai được chuẩn bị từ `main` tại `d93826c74b8b4a0228eab2e4af785a12cf826c22`, trên nhánh `feat/week3-observability-benchmark`.

## Thành phần trong repository

| Mã | Thành phần | Files chính | Nội dung |
| --- | --- | --- | --- |
| W3-01 | Monitoring | `iac/week3-monitoring.yaml`, `scripts/collect_cloudwatch_metrics.py` | Alarm DLQ visible messages >=1, QueueName dimension, tham chiếu SNS ARN hiện có, kiểm tra region của stack; collector SQS/Lambda/alarm. |
| W3-02 | SQS API benchmark | `scripts/benchmark_sqs.py`, `tests/test_benchmark_sqs.py` | Standard/FIFO, group/dedup, thống kê send/receive/duplicate/order, xác minh message thuộc lần gửi trước khi delete, JSON/CSV. |
| W3-03 | Load và reconciliation | `scripts/load_test_orders.py`, `scripts/test-order-api.ps1`, `tests/test_load_test_orders.py` | Endpoint cấu hình được, tải tuần tự có giới hạn, HTTP 202 và orderId, GetItem chỉ đọc theo orderId, giới hạn polling và lỗi. |
| W3-04 | Metrics/report | `scripts/collect_cloudwatch_metrics.py`, `scripts/generate_week3_report.py` | UTC, raw datapoints và summary, xử lý dữ liệu thiếu, Markdown từ JSON, giữ nhãn synthetic/dry-run của dữ liệu đầu vào. |
| W3-05 | Regression | `tests/test_producer.py`, `tests/test_consumer.py`, ba tệp test Tuần 3 | Bảo toàn 33 test methods gốc; bổ sung tests cho công cụ và các nhánh lỗi. |
| W3-06 | CI definition | `.github/workflows/python-tests.yml` | PR/push vào main, Python, pytest/unittest/compile, kiểm tra template và CLI; `contents: read`, không cấu hình deploy. |
| W3-07 | Tài liệu | `docs/week3-*.md`, `docs/WEEK3_AGENT_HANDOFF.md`, `docs/evidence/week3/README.md` | Kế hoạch, hướng dẫn công cụ, schema output, runbook thao tác và danh mục loại evidence. |

## Ranh giới kỹ thuật

- Source Producer/Consumer và hợp đồng dữ liệu giữ nguyên; HTTP 202 thể hiện tiếp nhận vào SQS, còn DynamoDB PROCESSED thể hiện bước xử lý Consumer.
- Benchmark chỉ sử dụng queue thử riêng, chặn `orders-queue` và `orders-dlq`; không purge hoặc tạo/xóa queue từ script.
- Các CLI mặc định không gọi mạng; benchmark/load dùng `--execute` cùng target confirmation, collector chỉ đọc dùng `--execute`. Các cờ dry-run và execute mâu thuẫn bị từ chối.
- Load gửi tuần tự. Giới hạn rate của client không tự bảo đảm tổng concurrency của cả tài khoản; khi vận hành, đối chiếu cấu hình Lab theo runbook.
- Chỉ đưa số đo từ file đầu vào thực tế vào báo cáo; dữ liệu synthetic/dry-run giữ nhãn nguồn tương ứng.

## Schema dữ liệu đầu ra 1.0

Các JSON dùng `schemaVersion: "1.0"`, `runId` dạng string và `executeMode` dạng boolean. Timestamp dùng ISO-8601 UTC; count là integer, latency theo ms và throughput theo message/giây. Giá trị chưa đo dùng `null`/trạng thái thiếu dữ liệu; không diễn giải metric dry-run bằng số 0 thành phép đo AWS.

| Nguồn | Tệp JSON / CSV | Các cấu trúc chính |
| --- | --- | --- |
| SQS API | `benchmark-summary.json` / `benchmark-results.csv` | JSON: `configuration`, `metrics`, `ordering`, `records`, `limitations`; CSV mỗi send/receive có `runId`, `phase`, `sequenceNumber`, `orderId`, `messageGroupId`, `sqsMessageId`, `status`, `latencyMs`, `errorCode`. |
| API load + DynamoDB | `load-test-summary.json` / `load-test-results.csv` | JSON: `configuration`, `summary`, `reconciliation`, `requests`; CSV mỗi request có `runId`, `requestId`, `timestampUtc`, `httpStatus`, `responseTimeMs`, `orderId`, `errorCategory`, `reconciledState`. |
| CloudWatch | `cloudwatch-metrics-summary.json` / `cloudwatch-metrics-results.csv` | JSON: `collectedAt`, `region`, `windowStart`, `windowEnd`, `periodSeconds`, `metrics`, `alarms`; CSV ghi resource/namespace/metric/statistic, cửa sổ thời gian, trạng thái, số datapoint, giá trị tổng hợp hoặc ô trống và mã lỗi. |

`generate_week3_report.py` đọc các JSON này và sinh Markdown; không đọc CSV trực tiếp. Report giữ nhãn nguồn, dry-run/synthetic và phần AWS chưa xác minh. File output local có thể chứa tên resource hoặc orderId cần đối soát; chỉ công bố bản đã che thông tin theo evidence checklist.


## Kiểm thử đã thực hiện (Kết quả offline lịch sử)

Môi trường local: Python 3.14.5, pytest 9.1.1, boto3 1.43.118, PyYAML 6.0.3, cfn-lint 1.58.0.

| Kiểm tra | Kết quả quan sát |
| --- | --- |
| `python -B -m pytest -q tests/test_monitoring_and_metrics.py tests/test_benchmark_sqs.py tests/test_load_test_orders.py` | 21 passed, 23 subtests passed; 0 failed, 0 skipped. |
| `python -B -m pytest -q` | 54 passed, 104 subtests passed; 0 failed, 0 skipped. |
| `python -B -m unittest discover -s tests -p "test_*.py"` | Ran 54 tests; OK, exit 0. |
| `python -m compileall -q src scripts tests` | Exit 0. |
| `cfn-lint iac/week3-monitoring.yaml` | Exit 0 trên template có ràng buộc region (và được thực thi tự động trong `.github/workflows/python-tests.yml`). |
| GitHub Actions CI | Baseline commit `710c8f0` hoàn tất tại run [`39987033004`](https://github.com/pminhquan/cloud-async-orders/actions/runs/39987033004) (`Python Regression & Offline IaC Validation`, `status=completed`, `conclusion=success`); trạng thái CI của HEAD hiện tại và SHA/kết quả cuối cùng được ghi nhận tại [PR #11 Checks](https://github.com/pminhquan/cloud-async-orders/pull/11/checks) và phần mô tả của PR #11. |
| So sánh source và hai tệp regression gốc với base commit | Không đổi; 33 test methods gốc được giữ nguyên. |
| CLI offline | 9 ca help/default dry-run/từ chối queue chính qua khi socket và SDK client/resource bị chặn. |
| Report CLI trên cp1252 Windows | Exit 0; tệp UTF-8 hợp lệ, giữ nhãn dry-run và bỏ phần không có input. |
| PowerShell wrapper dry-run | Exit 0. |

Bộ test gồm 18 Producer, 15 Consumer, 9 benchmark, 4 load/reconciliation và 8 monitoring/report methods (tổng 54 test methods, trong đó 21 methods thuộc bộ công cụ Tuần 3). Có regression cho giải phân giải URL queue (`GetQueueUrl`), message ownership, deadline/polling, SDK không retry ngầm, cờ mâu thuẫn, timestamp thiếu, giới hạn `<= 1440` datapoints của CloudWatch, dữ liệu report thiếu (bao gồm bảng trạng thái Alarm và phân rã đối soát DynamoDB) và encoding Windows.

---

# Kết quả kiểm thử vận hành thực tế Tuần 3 (Phase B1 & B2 — 24/10/2026)

## 1. Đo kiểm độc lập SQS Standard vs FIFO (Phase B1)

Kết quả đo kiểm SQS API độc lập đã hoàn tất và được tích hợp qua [PR #13](https://github.com/pminhquan/cloud-async-orders/pull/13). Báo cáo phân tích chi tiết được lưu trữ tại [`docs/week3-quan-b1-results.md`](week3-quan-b1-results.md) cùng thư mục minh chứng [`docs/evidence/week3/quan/b1-2026-10-24/`](evidence/week3/quan/b1-2026-10-24/).
- Ba kịch bản đo kiểm độc lập (20 messages mỗi kịch bản, 60 messages tổng cộng) trên 2 hàng đợi thử nghiệm cách ly (`orders-benchmark-standard` và `orders-benchmark.fifo`), dọn sạch 60/60 messages sau khi nhận.
- Báo cáo tổng hợp này không sao chép lại bảng số liệu B1; số đo hiệu năng và phân tích đối chiếu trực tiếp từ báo cáo B1 chuyên sâu và tệp manifest tương ứng.

## 2. Minh chứng giám sát và cảnh báo từ Khôi

Minh chứng cảnh báo và xác thực thành phần Producer / API được ghi nhận tại [`docs/week3-khoi-evidence.md`](week3-khoi-evidence.md) và thư mục ảnh [`docs/evidence/week3/khoi/`](evidence/week3/khoi/):
- Xác nhận subscription SNS Topic `order-dlq-alert` (giao thức Email) và kiểm tra publish thử nghiệm thành công.
- Lưu ý kỹ thuật: Ảnh lịch sử CloudWatch Alarm (`W3-CW-DLQ-Alarm-History.png`) và email cảnh báo nhận được phản ánh phép thử kích hoạt trạng thái alarm thủ công (xem [`docs/week3-khoi-evidence.md`](week3-khoi-evidence.md)), không phải do tự động tích tụ backlog trong phép đo này.
- Tài nguyên SNS/Alarm trong minh chứng của Khôi được kiểm thử trên môi trường riêng của Khôi; không suy diễn tài nguyên này tồn tại sẵn trên tài khoản thực thi của Quân. Trạng thái `NOT_FOUND` của alarm trên tài khoản của Quân chỉ thể hiện tên alarm đó vắng mặt tại thời điểm kiểm tra, không khẳng định CloudFormation chưa từng được triển khai.

## 3. Kiểm thử vận hành trực tiếp toàn trình (Phase B2)

Kịch bản Phase B2 được người dùng phê duyệt chạy đúng **01 lần duy nhất** vào ngày 24/10/2026 trên AWS Account `<ACCOUNT_ID>` (`us-east-1`). Toàn bộ minh chứng chuẩn hóa được công bố tại [`docs/evidence/week3/quan/b2-2026-10-24/`](evidence/week3/quan/b2-2026-10-24/).

### 3.1. Trạng thái bất biến & Quy trình bảo vệ Try/Finally
- **Kiểm tra trước thực thi:** Lúc `12:28:50Z`, kiểm tra đối soát control-plane xác nhận STS caller identity, mã băm Lambda deployed (Producer `AVeX+UvbRSOL/m7KEdY+vPO2B6dhwv/lozuHAvUoLMk=`, Consumer `cAglL/yZX4JdPU+NM3pAYTTK5C4hG11FopmcTbYZLpA=`), cả 2 ESM ở trạng thái `Disabled`, bảng `Orders` ở trạng thái `ACTIVE`, route API Gateway `POST /orders` hợp lệ, và cả 2 hàng đợi benchmark giữ nguyên `0/0/0`. Ngay trước khi kích hoạt (`12:29:35Z`), `orders-queue` có `0/0/0` và `orders-dlq` có `2/0/0`.
- **Kích hoạt ESM Consumer:** ESM `ab1f7f06-157c-429b-bfcf-5cb15689f47f` được gửi lệnh kích hoạt lúc `12:29:36Z` và quan sát đạt trạng thái `Enabled` lúc `12:29:52Z`. ESM legacy `7812ff9b-4000-47e1-9e27-6805670c7cc6` giữ nguyên `Disabled` xuyên suốt.
- **Hoàn nguyên an toàn trong khối finally:** Lệnh khôi phục ESM về `Disabled` được phát đi lúc `12:30:11Z` và xác nhận đạt trạng thái `Disabled` lúc `12:30:17Z` (khoảng thời gian quan sát từ lúc bắt đầu `Enabled` đến khi xác nhận `Disabled` bao gồm thời gian thăm dò chuyển trạng thái).
- **Kiểm tra sau thực thi & Bằng chứng nguyên vẹn DLQ:**
  - Hàng đợi `orders-queue` trống hoàn toàn (`0/0/0`). Cả 2 hàng đợi benchmark giữ nguyên `0/0/0`.
  - Hàng đợi `orders-dlq` giữ nguyên chính xác `2/0/0` messages lịch sử.
  - **Bằng chứng thao tác:** Quá trình chạy B2 ghi nhận đúng **0** lệnh `ReceiveMessage`, **0** lệnh `DeleteMessage`, **0** lệnh `DeleteMessageBatch`, và **0** lệnh `PurgeQueue` đối với `orders-dlq`. Duy nhất 2 lệnh đọc chỉ số `GetQueueAttributes` được gọi, chứng minh danh tính 2 message lịch sử không bị can thiệp (chỉ số đếm không tự coi là bằng chứng danh tính độc lập).

### 3.2. Kết quả kiểm thử tải API & Đối soát DynamoDB (W3-03)
- **Mã lần chạy (`runId`):** `b2-run-20261024T122952Z-01`
- **Thời gian thực thi (UTC):** `2026-10-24T12:29:52Z` đến `2026-10-24T12:30:11Z`
- **Cấu hình:** Endpoint `POST https://<API_ID>.execute-api.us-east-1.amazonaws.com/orders`, số lượng 10 requests, tốc độ 2.0 req/s, `customerPrefix = CUS-B2-20261024`, `productId = P001`, `tableName = Orders`.
  - *Lưu ý về quy mô:* Số lượng 10 requests là quyết định phạm vi rõ ràng được người dùng phê duyệt cho lần chạy trực tiếp này (giảm từ mức 20 trong runbook); thông lượng khi chịu tải duy trì lâu hơn chưa được xác minh.
- **Kết quả HTTP API:**
  - 10/10 requests được chấp nhận với HTTP 202 (`0` lỗi HTTP 4xx/5xx/timeout, `0` lần thử lại).
  - Tổng thời gian gửi: **13.8146 giây**.
  - Phân bố độ trễ API: Min **811.383 ms**, Median **824.446 ms**, Mean **931.091 ms**, P95 **1798.399 ms**, Max **1798.399 ms**.
  - *Ghi chú độ trễ:* Request đầu tiên có độ trễ cao nhất (1798.399 ms) với nguyên nhân cụ thể chưa được đo đạc trực tiếp (UNKNOWN); không giả định đây là cold start của API Gateway. Các request tiếp theo (req 2 đến req 10) đạt độ trễ ổn định trong khoảng 811.38 ms – 881.38 ms.
- **Đối soát DynamoDB (`GetItem` consistent read):**
  - Trạng thái đối soát: `ALL_PROCESSED` (10/10 đơn hàng).
  - Hoàn tất ngay trong **1 chu kỳ thăm dò duy nhất** (thời gian đối soát: **3.5846 giây**).
  - Không có đơn hàng nào ở trạng thái pending (`0`), thiếu (`NOT_FOUND = 0`), hay chưa xác minh (`0`).

### 3.3. Số liệu CloudWatch Metrics (W3-01 & W3-04)
- **Cửa sổ quan sát:** `2026-10-24T12:26:36Z` đến `2026-10-24T12:33:18Z` (Period 60s).
- **Mã lần chạy metrics chính thức:** `metrics-20261024T123957Z-59926310` (thực hiện lúc `12:39:57Z`, khi toàn bộ cửa sổ quan sát đã kết thúc trong quá khứ - closed observation window).
- **Ghi chú minh bạch về lần thu thập ban đầu:** Lần thu thập sơ bộ lúc `12:31:18Z` có cấu hình `windowEnd` lúc `12:33:18Z` (+120s buffer so với thời điểm gọi). Bản chụp thô ban đầu được bảo toàn nguyên vẹn trong `raw-b2/metrics/` và được thay thế chính thức bằng lần thu thập khép kín `raw-b2/metrics-final/` trong kho tài liệu minh chứng.
- **Số liệu CloudWatch đo được:**
  - `orders-queue`: `NumberOfMessagesSent = 10.0`, `NumberOfMessagesReceived = 10.0`, `NumberOfMessagesDeleted = 10.0`, `ApproximateNumberOfMessagesVisible = 0.0`.
  - `orders-dlq`: `NumberOfMessagesSent = 0.0` (chỉ số này phản ánh số message đẩy vào queue trong cửa sổ đo, không tự chứng minh cơ chế redrive tự động), `NumberOfMessagesReceived = 0.0`, `NumberOfMessagesDeleted = 0.0`, `ApproximateNumberOfMessagesVisible = 2.0`.
  - `order-producer`: `Invocations = 10.0`, `Errors = 0.0`, `Throttles = 0.0`.
  - `order-consumer`: `Invocations = 10.0`, `Errors = 0.0`, `Throttles = 0.0`, `ConcurrentExecutions` Max = 3.0.
  - Alarm `AsyncOrderProcessing-orders-dlq-VisibleMessages`: Trạng thái `NOT_FOUND` (tên alarm vắng mặt trên tài khoản thực thi tại thời điểm kiểm tra).

## 4. Sai lệch mã nguồn Producer & Giới hạn kỹ thuật

1. **Sai lệch kiểm tra đầu vào của Producer deployed (Validation Drift):**
   - Mã nguồn `order-producer` trên Lambda có timestamp `2026-10-15T11:09:32Z` (trước thời điểm tích hợp PR #7).
   - Bản deployed này thiếu hàm `_validate` để trả về HTTP 400 khi thiếu trường (nó tự gán `UNKNOWN` và `quantity=1`), và trả HTTP 500 khi gặp JSON sai cú pháp.
   - Khi chạy bài test B2 với 10 payload chuẩn gồm đầy đủ `{customerId, productId, quantity}`, Producer xử lý hoàn toàn hợp lệ và trả về HTTP 202. Mã nguồn deployed được giữ nguyên để tuân thủ phạm vi quyền hạn được cấp phép.
2. **Minh chứng giao diện AWS Management Console:**
   - Phiên làm việc trên browser hiện tại chưa xác thực đăng nhập IAM/SSO vào AWS Console, và môi trường không có công cụ chụp màn hình native.
   - Nhóm không tạo ảnh dựng hay mockup giả mạo. Các ảnh chụp Console riêng của Quân còn thiếu gồm: trạng thái Event Source Mapping của Consumer, giao diện API load / đối soát DynamoDB, và biểu đồ CloudWatch Metrics tương ứng. Bằng chứng kỹ thuật được bảo đảm thông qua dữ liệu đo kiểm thô (JSON/CSV), nhật ký thực thi chi tiết, mã băm SHA-256 trong `manifest.json` và số liệu API chính thức từ AWS.

## 5. Cập nhật Kiểm thử Hồi quy (Regression & CI Status)

- **Kiểm thử offline hiện tại:** Bộ test suite Tuần 3 (bao gồm bổ sung `NoRedirectHandler` và test regression chuyển hướng cho script load) đạt **56 passed, 114 subtests passed** trong 5.68s (trích xuất từ kết quả thực thi kiểm thử cục bộ Job 006).
- **Linter CloudFormation:** `cfn-lint iac/week3-monitoring.yaml` đạt kết quả exit 0.
- **Trạng thái GitHub Actions CI:** Trạng thái CI cho commit của PR cuối cùng được đối chiếu tại tab Checks và phần Validation trong mô tả PR; không suy từ CI lịch sử.
