# Kiểm thử hồi quy offline — 29/10/2026

## 1. Phạm vi và môi trường

Source ứng dụng, tests, scripts, IaC và CI tương đương mã nguồn tham chiếu `8b14e02ae64cc1a12e11d66c3f552824f67ab4b7`. Kiểm thử dùng môi trường Python **3.14.5** đã cài đặt; unit tests mô phỏng SQS/DynamoDB. CLI help/dry-run không thực hiện thao tác AWS.

## 2. Kết quả thực thi

| Kiểm tra | Kết quả |
|---|---|
| `python -B -m pytest -q -p no:cacheprovider` | 56 passed, 114 subtests passed in 6.64s |
| `python -B -m unittest discover -s tests -p "test_*.py"` | Ran 56 tests in 5.451s; OK |
| `python -m compileall -q src scripts tests` | Exit 0; bytecode cache ở thư mục tạm |
| `cfn-lint iac/week3-monitoring.yaml` | Exit 0 |
| `--help`: collect_cloudwatch_metrics, benchmark_sqs, load_test_orders, generate_week3_report | 4/4 exit 0 |
| Collector `--dry-run`, benchmark Standard `--dry-run`, load endpoint ví dụ `--dry-run` | 3/3 exit 0 |

Đầu ra pytest:

```text
56 passed, 114 subtests passed in 6.64s
```

Bộ kiểm thử Producer trước nghiệm thu AWS đạt 18 tests/7 subtests. Kết quả hồi quy và dry-run xác minh logic source, không thay cho bằng chứng deployment hoặc dữ liệu AWS. [Nghiệm thu AWS](../../week4-report.md) đối soát riêng API, Orders, retry và metrics.

## 3. Nhận diện source

SHA-256 tính sau khi chuẩn hóa CRLF thành LF:

| Source | SHA-256 |
|---|---|
| Producer | `54d8014411164db8c43e7adee60867a1e6167be7ccbc00f103bffb7cba64bc1b` |
| Consumer | `a4f54eb6df0a6da36e40b1fa0dff69c1de339b454f39d4909556e1066ae8e4b7` |

## 4. CI của mã nguồn tham chiếu

[Actions run 40163636601](https://github.com/pminhquan/cloud-async-orders/actions/runs/40163636601) có head SHA `8b14e02ae64cc1a12e11d66c3f552824f67ab4b7`, trạng thái completed/success. Kết quả này thuộc source tham chiếu. CI của mỗi PR phải được nhận diện bằng head SHA tương ứng, không dùng một run cũ để xác nhận tài liệu trên head khác.
