# Bàn giao triển khai offline Tuần 3

- Repository: `cloud-async-orders`.
- Base commit: `d93826c74b8b4a0228eab2e4af785a12cf826c22`.
- Branch local: `feat/week3-observability-benchmark`.

## Mã nguồn và hướng dẫn

| Thành phần | Tài liệu |
| --- | --- |
| CloudWatch/SNS IaC và collector | [Monitoring](week3-monitoring.md), [template](../iac/week3-monitoring.yaml) |
| SQS Standard/FIFO benchmark | [Benchmark](week3-benchmark.md) |
| Tải API và GetItem reconciliation | [Load testing](week3-load-testing.md) |
| Schema output và kết quả offline | [Báo cáo kỹ thuật](week3-report.md) |
| Thao tác Lab và loại evidence cần thu | [Runbook](week3-aws-manual-runbook.md), [evidence guide](evidence/week3/README.md) |

## Cấu hình công cụ

| Tham số | Ý nghĩa |
| --- | --- |
| `AWSRegionName`, `--region` | Region của stack/collector, mặc định us-east-1. |
| `AlertSnsTopicArn` | ARN topic SNS hiện có, truyền khi triển khai template. |
| `--queue-url`, `--queue-type`, `--group-count` | Queue thử và cấu hình Standard/FIFO. |
| `--endpoint` | HTTPS endpoint truyền cho công cụ load. |
| `--confirm-target` | Tên queue benchmark hoặc hostname API, dùng với execute của benchmark/load. |
| `--execute` | Opt-in mạng; collector chỉ đọc không yêu cầu confirm-target. |
| `--timeout`, `--max-polls`, `--reconcile-timeout`, `--reconcile-max-polls` | Ngân sách và giới hạn thao tác của công cụ tương ứng. |
| `--output-dir`, `--output` | Vị trí lưu dữ liệu/report local. |

## Lệnh kiểm tra offline

```text
python -m pytest -q
python -B -m unittest discover -s tests -p "test_*.py"
python -m compileall -q src scripts tests
cfn-lint iac/week3-monitoring.yaml
git diff --check
```

Dùng Python có các package `pytest`, `boto3`, `PyYAML`; `cfn-lint` phục vụ kiểm tra template. Source Producer/Consumer và hai tệp test regression gốc được giữ nguyên.


## Commit local

| SHA | Nội dung |
| --- | --- |
| eb47cc0 | docs: remove work-time attestations from course reports |
| e5f0487 | feat(week3): add bounded SQS benchmark and order load tools |
| 50b1e51 | feat(week3): add CloudWatch monitoring and measured report tools |
| af72a13 | ci: run offline Python regression and CLI checks |

## Kết quả kiểm thử

Python 3.14.5: pytest 53 passed và 94 subtests passed; unittest Ran 53 tests, OK. Compileall exit 0, cfn-lint exit 0, các kiểm tra CLI offline và report CLI cp1252 đều qua. Chi tiết lệnh, phiên bản và phạm vi test tại [báo cáo offline](week3-report.md).

Source Producer/Consumer và hai tệp test gốc khớp byte với base commit. Bộ kiểm thử gồm 33 methods gốc và 20 methods mới. Tham số thực thi, ranh giới thao tác và ngân sách polling được mô tả trong tài liệu từng công cụ.
