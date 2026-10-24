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


## Kiểm thử đã thực hiện

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
