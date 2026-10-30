# Ma trận nghiệm thu kỹ thuật Tuần 4

Ngày nghiệm thu: **29–30/10/2026**. Môi trường thực nghiệm là Lab Quân; dữ liệu Tuần 3 và minh chứng monitoring Khôi được dẫn theo đúng ngày và môi trường.

| Mã | Tiêu chí đối chiếu | Kết quả và tài liệu |
|---|---|---|
| W4-01 | Kiểm kê tài nguyên và source triển khai | Đối chiếu API, queue, mapping, Lambda và Orders; [inventory nghiệm thu](week4-report.md) |
| W4-02 | Luồng từ API tới cơ sở dữ liệu | Producer đúng source tham chiếu, mapping Enabled; HTTP 202 và đúng orderId PROCESSED; [E2E](week4-report.md) |
| W4-03 | Validation và bảo vệ dữ liệu | 13/13 HTTP đúng kỳ vọng, replay/conflict giữ item, năm lần lỗi và tương quan DLQ; [ma trận kiểm thử](week4-report.md) |
| W4-04 | Giám sát và phân phối cảnh báo | Lab Quân ngày 30/10: DLQ metric 1.0 → ALARM → SNS action thành công → email khớp; [minh chứng](evidence/week4/README.md) |
| W4-05 | Phân tích hiệu năng có căn cứ | B1/B2/B3 giữ đúng điều kiện và giới hạn mẫu; [đánh giá](week4-report.md#51-hiệu-năng-từ-minh-chứng-hiện-có) |
| W4-06 | Đánh giá chi phí | Sáu yếu tố dịch vụ và nguồn giá chính thức; [phân tích chi phí](week4-cost-analysis.md) |
| W4-07 | Quản lý tài nguyên và minh chứng | Giữ tài nguyên đối soát, không purge/delete; [trạng thái cuối](week4-report.md) |
| W4-08 | Hồi quy và tính nhất quán source | 56 tests/114 subtests, unittest 56, compile/lint và bảy CLI checks; [kết quả offline](evidence/week4/offline-validation.md) |
| W4-09 | Tổng hợp học thuật | [Báo cáo Tuần 4](week4-report.md), [traceability](traceability.md), [kịch bản demo](demo-script.md) và [khai báo AI](ai-declaration.md) |

Kết quả chỉ áp dụng phạm vi thử nghiệm đã mô tả. Retry/redrive là bằng chứng tương quan cấu hình/log/số lượng, chưa kiểm tra body DLQ. Cảnh báo metric-driven Lab Quân đã xác minh riêng; minh chứng Khôi giữ phạm vi thủ công. Mẫu nhỏ chưa chứng minh năng lực production.
