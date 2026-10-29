# Kết quả triển khai offline Tuần 3

> Tài liệu giữ kết quả và kế hoạch lịch sử Tuần 3. Kết quả thực thi ngày 29/10/2026 nằm trong [báo cáo Tuần 4](week4-report.md); Producer drift và ESM Disabled mô tả bên dưới là trạng thái trước khi xử lý Tuần 4.


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

# Kết quả kiểm thử vận hành thực tế Tuần 3 (Phase B1, B2 & B3 — 24/10/2026)

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
  - **Bảo toàn hàng đợi DLQ qua nguyên tắc không can thiệp (Non-interference):** Quá trình chạy B2 ghi nhận đúng **0** lệnh đọc (`ReceiveMessage`), **0** lệnh ghi/xóa (`DeleteMessage`, `DeleteMessageBatch`, `PurgeQueue`) đối với `orders-dlq`. Chỉ số đếm trước và sau thực thi đều giữ nguyên `2/0/0`. Việc không phát sinh bất kỳ lệnh đọc hay can thiệp nào khẳng định các message lịch sử được bảo toàn nguyên vẹn; danh tính nội dung chi tiết của từng message không được đọc hay đối chiếu độc lập.

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

### 3.4. Kết quả kiểm thử xử lý theo lô B3 (Batch Processing - BatchSize=2, BatchingWindow=5s)
- **Mã lần chạy (`runId`):** `b3-run-20261024T160006Z-63133f25`
- **Thời gian thực thi (UTC):** `2026-10-24T15:59:50Z` đến `2026-10-24T16:00:35Z` (kiểm tra trạng thái đối soát cuối lúc `16:05:41Z`).
- **Phê duyệt phạm vi:** Phase B3 gồm đúng **02 đơn hàng hợp lệ bổ sung** được người dùng phê duyệt riêng biệt (với tốc độ $\le 2\text{ req/s}$), tiếp nối sau Phase B2 gồm 10 đơn hàng (được giảm từ mức 20 trong runbook theo phê duyệt phạm vi).
- **Cấu hình:** Consumer timeout tạm thời tăng lên 8s; ESM `ab1f7f06-157c-429b-bfcf-5cb15689f47f` tạm thời cấu hình `BatchSize=2`, `MaximumBatchingWindowInSeconds=5`, sau đó kích hoạt `Enabled`.
- **Thực thi tải & Thiết kế đối soát:**
  - Gửi đúng 2 orders hợp lệ (`e40094f0-f303-4eca-be0a-0fb57b1836c1`, `12c1bb70-25eb-43b2-936f-ee62714236b5`) qua API POST với tốc độ $\le 2\text{ req/s}$; cả 2/2 requests được chấp nhận HTTP 202.
  - *Thiết kế đối soát B3:* Lệnh chạy load script cấu hình `reconcileEnabled: false` theo chủ đích thiết kế để không thực hiện polling DynamoDB khi ESM đang Disabled; việc đối soát `GetItem` được script wrapper thực hiện trực tiếp sau khi kích hoạt ESM và được ghi nhận đầy đủ trong [`b3-execution-log.json`](evidence/week3/quan/b3-2026-10-24/b3-execution-log.json) (bảo toàn nguyên vẹn tệp dữ liệu thô `load-test-summary.json`).
- **Đối soát DynamoDB:** Cả 2 đơn hàng đều ghi nhận trạng thái `PROCESSED` thành công trong DynamoDB `Orders`.
- **Bằng chứng xử lý lô CloudWatch Logs (`batch-proof.json` & ảnh chụp Console):**
  - Xác nhận cả 2 message SQS (`6e052d51-b729-43fa-aa71-ecf74384582f`, `fa670c23-cfcc-4b62-808a-3bca29c7711e`) được xử lý trong **cùng 1 invocation** duy nhất của Consumer Lambda:
  - Lambda RequestId: `669f8c38-d85a-55dd-9a5a-ef6e0015632a`
  - Log Stream: `2026/10/24/[$LATEST]81bcb1adbd6d4fadbf89bcddc1372c8d`
  - Thời lượng thực thi: Duration 2784.26 ms, Billed Duration 3139 ms.
  - Cả 2 log event `[INFO] ... "status": "PROCESSED"` tương ứng với 2 orderId nằm trọn vẹn giữa START và END/REPORT của cùng RequestId.
  - Minh chứng trực quan: Bản chụp AWS Console CloudWatch log events được lưu tại [`docs/evidence/week3/quan/b3-2026-10-24/screenshots/W3-B3-CloudWatch-Two-Record-Batch.jpg`](evidence/week3/quan/b3-2026-10-24/screenshots/W3-B3-CloudWatch-Two-Record-Batch.jpg) (xem [`screenshots-provenance.json`](evidence/week3/quan/b3-2026-10-24/screenshots/screenshots-provenance.json)).
- **Hoàn nguyên an toàn & Báo cáo trung thực số liệu hàng đợi:**
  - Timeout Consumer được hoàn nguyên về mức mặc định 3s (`timeoutRestoreConfirmedAtUtc: 16:00:35Z`).
  - ESM Consumer được hoàn nguyên về trạng thái `Disabled`, `BatchSize=1`, `MaximumBatchingWindowInSeconds=0` (`esmRestoreConfirmedAtUtc: 16:00:31Z`).
  - ESM legacy giữ nguyên `Disabled`.
  - Hàng đợi `orders-dlq` giữ nguyên chính xác `2/0/0` messages lịch sử (0 thao tác can thiệp).
  - *Số liệu đếm hàng đợi chính (`orders-queue`):* Tại thời điểm hoàn tất chạy B3 (`16:00:35Z`), chỉ số SQS xấp xỉ ghi nhận thô là `2/0/0` (visible: 2, notVisible: 0, delayed: 0); tệp kiểm tra trạng thái cuối [`final-state-check.json`](evidence/week3/quan/b3-2026-10-24/final-state-check.json) (thực hiện lúc `16:05:41Z`) xác nhận `orders-queue` trống hoàn toàn (`0/0/0`). Độ trễ cập nhật xấp xỉ của SQS là một suy luận kỹ thuật; cả hai giá trị thô quan sát được đều được báo cáo minh bạch, không sửa đổi dữ liệu gốc.

## 4. Sai lệch mã nguồn Producer & Giới hạn kỹ thuật

1. **Sai lệch kiểm tra đầu vào của Producer deployed (Validation Drift):**
   - Mã nguồn `order-producer` trên Lambda có timestamp `2026-10-15T11:09:32Z` (trước thời điểm tích hợp PR #7).
   - Bản deployed này thiếu hàm `_validate` để trả về HTTP 400 khi thiếu trường (nó tự gán `UNKNOWN` và `quantity=1`), và trả HTTP 500 khi gặp JSON sai cú pháp.
   - Khi chạy bài test B2 với 10 payload chuẩn gồm đầy đủ `{customerId, productId, quantity}`, Producer xử lý hoàn toàn hợp lệ và trả về HTTP 202. Mã nguồn deployed được giữ nguyên để tuân thủ phạm vi quyền hạn được cấp phép.
2. **Minh chứng giao diện trực quan (Visual Evidence):**
   - **Minh chứng Phase B2 (5 ảnh):** Đã thu thập và lưu trữ tại [`docs/evidence/week3/quan/b2-2026-10-24/screenshots/`](evidence/week3/quan/b2-2026-10-24/screenshots/) kèm [`screenshots-provenance.json`](evidence/week3/quan/b2-2026-10-24/screenshots/screenshots-provenance.json):
     - `W3-B2-Consumer-Disabled.jpg` (AWS Console crop): Giao diện cấu hình trigger Lambda `order-consumer` thể hiện Event Source Mapping ở trạng thái Disabled (batch size 1, window None).
     - `W3-B2-CloudWatch-Consumer.jpg` (AWS Console crop): Widget CloudWatch tích hợp trong tab Monitor của Lambda `order-consumer` ghi nhận 10 invocations.
     - `W3-B2-DynamoDB-Console-Order.jpg` (AWS Console crop): Chi tiết item đơn hàng B2 `1145a7cf-4861-4d3c-b90b-8c2cfe66d07d` trong bảng `Orders` ở trạng thái `PROCESSED` (truy vấn theo partition key, dùng Cancel để đóng, không lưu thay đổi).
     - `W3-B2-API-Recorded-Results.jpg` (Recorded SDK view): Bản chụp trình duyệt hiển thị tệp kết quả thực thi kiểm thử tải ghi nhận 10/10 HTTP 202 accepted và 0 lỗi.
     - `W3-B2-DynamoDB-Recorded-GetItem.jpg` (Recorded SDK view): Bản chụp trình duyệt hiển thị tệp đối soát DynamoDB GetItem ghi nhận toàn bộ 10 đơn hàng đạt trạng thái PROCESSED trong 3.5846 giây.
   - **Minh chứng Phase B3 (1 ảnh):** Đã thu thập và lưu trữ tại [`docs/evidence/week3/quan/b3-2026-10-24/screenshots/`](evidence/week3/quan/b3-2026-10-24/screenshots/) kèm [`screenshots-provenance.json`](evidence/week3/quan/b3-2026-10-24/screenshots/screenshots-provenance.json):
     - `W3-B3-CloudWatch-Two-Record-Batch.jpg` (AWS Console crop): Trình xem log CloudWatch của `order-consumer` thể hiện 2 bản ghi INFO PROCESSED hoàn chỉnh (kèm đầy đủ orderId và messageId) nằm giữa START và END/REPORT trong cùng RequestId `669f8c38-d85a-55dd-9a5a-ef6e0015632a`.
   - Toàn bộ ảnh được lưu giữ nguyên gốc với mã băm SHA-256 được kiểm tra đối chiếu; vùng tài khoản và thông tin cá nhân được che/cắt bằng native crop tự nhiên khi lưu.

## 5. Cập nhật Kiểm thử Hồi quy (Regression & CI Status)

- **Kiểm thử offline hiện tại:**
  - Bộ unit test chạy trực tiếp: `python -m unittest discover -s tests -v` đạt **56 passed** trong 5.616s.
  - Bộ kiểm thử hồi quy đầy đủ: `pytest` đạt **56 passed, 114 subtests passed** (ghi nhận từ phiên kiểm thử offline trước đó).
- **Linter CloudFormation:** `cfn-lint iac/week3-monitoring.yaml` đạt kết quả exit 0.
- **Trạng thái GitHub Actions CI:** Trạng thái CI cho commit của PR cuối cùng được đối chiếu trực tiếp tại tab Checks của [PR #14](https://github.com/pminhquan/cloud-async-orders/pull/14/checks); không suy từ CI lịch sử.

## 6. Bảng tổng hợp bàn giao nghiệm thu Tuần 3 (Handoff Summary)

| Mã hàng mục | Hạng mục (W3) | Trạng thái thực tế | Bằng chứng & Tham chiếu chéo |
|---|---|---|---|
| **W3-01** | CloudWatch Monitoring & DLQ Alarm | **HOÀN THÀNH** | Template `iac/week3-monitoring.yaml` (exit 0 cfn-lint); Tham chiếu chéo minh chứng của Khôi tại [`docs/week3-khoi-evidence.md`](week3-khoi-evidence.md) & [`docs/evidence/week3/khoi/`](evidence/week3/khoi/) (xác minh SNS Topic `order-dlq-alert`, subscription email confirmed và kích hoạt alarm thử nghiệm). Số liệu CloudWatch metrics B2 thu thập khép kín tại [`docs/evidence/week3/quan/b2-2026-10-24/metrics/`](evidence/week3/quan/b2-2026-10-24/metrics/). |
| **W3-02** | SQS Standard vs FIFO Benchmark | **HOÀN THÀNH** | Đã tích hợp qua [PR #13](https://github.com/pminhquan/cloud-async-orders/pull/13); Tham chiếu chéo báo cáo phân tích B1 tại [`docs/week3-quan-b1-results.md`](week3-quan-b1-results.md) và minh chứng độc lập tại [`docs/evidence/week3/quan/b1-2026-10-24/`](evidence/week3/quan/b1-2026-10-24/) (3 kịch bản x 20 messages, so sánh throughput/latency/ordering). |
| **W3-03** | Controlled Load Test & Batch Processing (B2 + B3) | **HOÀN THÀNH** | **Phase B2:** 10/10 orders HTTP 202, 10/10 DynamoDB PROCESSED trong 3.58s ([`docs/evidence/week3/quan/b2-2026-10-24/load/`](evidence/week3/quan/b2-2026-10-24/load/)).<br>**Phase B3:** 2/2 orders HTTP 202, 2/2 PROCESSED; chứng minh batch 2 bản ghi trong cùng Lambda RequestId `669f8c38-d85a-55dd-9a5a-ef6e0015632a` ([`docs/evidence/week3/quan/b3-2026-10-24/batch-proof.json`](evidence/week3/quan/b3-2026-10-24/batch-proof.json)). |
| **W3-04** | Metrics Collector, Safe Restoration & CI Status | **HOÀN THÀNH** | Tệp kiểm tra trạng thái cuối [`docs/evidence/week3/quan/b3-2026-10-24/final-state-check.json`](evidence/week3/quan/b3-2026-10-24/final-state-check.json) xác nhận: Consumer timeout = 3s, ESM Disabled, `orders-queue` = 0/0/0, `orders-dlq` = 2/0/0.<br>**Trạng thái CI:** Trực tiếp đối soát kết quả kiểm thử hồi quy tại [PR #14 Checks](https://github.com/pminhquan/cloud-async-orders/pull/14/checks); 56 unit test offline PASS (`tests/`). |

---

## 7. Kế hoạch Tuần 4 (C10)

Tuần 4 là giai đoạn hoàn thiện đề tài, tập trung vào kiểm thử tổng thể, tối ưu hiệu năng và chi phí AWS, dọn dẹp tài nguyên thử nghiệm, hoàn thiện báo cáo cuối kỳ và chuẩn bị demo.

### 7.1. Kiểm thử tổng thể

- Kiểm tra luồng API Gateway → Producer → SQS → Consumer → DynamoDB.
- Kiểm thử request hợp lệ và không hợp lệ.
- Kiểm tra idempotency, retry/DLQ và SQS batch.
- Đối soát orderId và trạng thái PROCESSED.
- Kiểm tra CloudWatch Alarm và SNS Email Alert.

### 7.2. Đánh giá và tối ưu chi phí AWS

- Đánh giá cấu hình và thời gian thực thi Lambda.
- Kiểm tra SQS request, batch size và message retention.
- Rà soát DynamoDB capacity và dữ liệu thử nghiệm.
- Đánh giá CloudWatch Logs, Metrics và Alarm.
- Đề xuất tối ưu chi phí phù hợp với AWS Learner Lab.

### 7.3. Dọn dẹp tài nguyên

- Kiểm kê SQS, DynamoDB, Lambda, CloudWatch và SNS.
- Lưu minh chứng và cấu hình cần thiết trước khi dọn dẹp.
- Chỉ xóa tài nguyên thử nghiệm không còn sử dụng sau khi demo hoàn tất và được chủ môi trường đồng ý.
- Kiểm tra lại trạng thái tài nguyên sau dọn dẹp.

### 7.4. Báo cáo và demo

- Tổng hợp kết quả bốn tuần thực hiện.
- Hoàn thiện báo cáo cuối kỳ và tài liệu GitHub.
- Chuẩn bị kịch bản demo API, SQS, DynamoDB, CloudWatch và SNS.
- Phân chia nhiệm vụ thuyết trình giữa Khôi và Quân.
- Chuẩn bị phương án dự phòng khi AWS Learner Lab gặp sự cố.

### 7.5. Phân công và tiêu chí nghiệm thu

| Công việc | Phụ trách |
|---|---|
| API Gateway, Producer và SNS | Khôi |
| Consumer, SQS/DLQ và DynamoDB | Quân |
| Kiểm thử E2E | Khôi, Quân |
| Đánh giá hiệu năng và chi phí | Quân, Khôi |
| Dọn dẹp tài nguyên AWS | Khôi, Quân |
| Báo cáo cuối kỳ và demo | Khôi, Quân |

Kết quả nghiệm thu dự kiến gồm: bảng kiểm thử tổng thể, đánh giá hiệu năng/chi phí, danh sách tài nguyên được rà soát, báo cáo cuối kỳ, kịch bản demo và minh chứng GitHub.

**Kế hoạch Tuần 4 chi tiết:** [docs/week4-plan.md](week4-plan.md)

**Trạng thái:** Kế hoạch dự kiến; kết quả thực hiện sẽ được cập nhật kèm minh chứng trong Tuần 4.
