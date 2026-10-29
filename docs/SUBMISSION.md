# Hướng dẫn hồ sơ học phần

## 1. Mã nguồn và tài liệu chính

Repository: [pminhquan/cloud-async-orders](https://github.com/pminhquan/cloud-async-orders).

| Thành phần | Tài liệu/đường dẫn |
|---|---|
| Báo cáo tổng kết bốn tuần | [final-report.md](final-report.md) |
| Nghiệm thu Tuần 4 | [week4-report.md](week4-report.md) |
| Đánh giá chi phí | [week4-cost-analysis.md](week4-cost-analysis.md) |
| Kịch bản thuyết trình | [demo-script.md](demo-script.md) |
| Đối chiếu yêu cầu và phân công | [Traceability](TRACEABILITY-W1-W2.md), [phân công](task-assignment.md) |
| Kiến trúc và hợp đồng | [Kiến trúc](architecture/README.md), [integration contract](integration-contract.md) |
| Khai báo công cụ hỗ trợ | [ai-declaration.md](ai-declaration.md) |

## 2. Kiểm thử và minh chứng

Hồi quy đạt **56 tests và 114 subtests**; unittest đạt **56 tests**. Compileall, cfn-lint và bảy kiểm tra CLI thành công. [Phương pháp và kết quả offline](evidence/week4/offline-validation.md) tách biệt kiểm thử mô phỏng với [nghiệm thu AWS](week4-report.md).

Nghiệm thu ngày 29/10 trên Lab Quân có HTTP 202 và item `PROCESSED` cùng orderId, 12 request invalid trả 400, replay/conflict giữ nguyên dữ liệu, năm lần lỗi sentinel và tương quan redrive. Benchmark/load/batch cùng bằng chứng Alarm/SNS của Khôi được ghi đúng ngày 24/10 và phạm vi thủ công.

[Minh chứng Tuần 1](evidence/week1/README.md), [Tuần 2](evidence/week2/README.md), [Tuần 3](evidence/week3/README.md), [Tuần 4](evidence/week4/README.md).

## 3. Nguồn tham chiếu và thay đổi

CI của mã nguồn `8b14e02ae64cc1a12e11d66c3f552824f67ab4b7` hoàn tất thành công tại [Actions run 40163636601](https://github.com/pminhquan/cloud-async-orders/actions/runs/40163636601). Đây là CI của nguồn tham chiếu; kết quả PR được đối chiếu riêng theo đúng head commit trên [GitHub Actions](https://github.com/pminhquan/cloud-async-orders/actions).

Nội dung Tuần 4 tập trung tài liệu và dẫn chiếu minh chứng, giữ nguyên source/tests/scripts/IaC/CI. [Ảnh AWS lịch sử của Khôi](week3-khoi-evidence.md) giữ bản chụp gốc và thông tin sinh viên để đối chiếu học phần. Các thay đổi được quản lý tại [Pull Requests](https://github.com/pminhquan/cloud-async-orders/pulls) theo [quy ước Git](../CONTRIBUTING.md).

## 4. Cấu trúc hồ sơ

Source ở `src/`, unit tests ở `tests/`, công cụ kiểm thử/thu metrics ở `scripts/`, template monitoring ở `iac/`, báo cáo và minh chứng ở `docs/`. Hồ sơ dùng cùng nguồn dữ liệu và dẫn chiếu theo tuần, không kèm credential hoặc cấu hình phục hồi riêng.

Video và nhật ký học phần do sinh viên quản lý riêng theo [yêu cầu dự án](requirements.md). Kịch bản mô tả cách trình bày, không xác nhận đã có bản ghi video.
