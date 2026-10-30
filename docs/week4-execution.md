# Ma trận nghiệm thu kỹ thuật Tuần 4

Ngày nghiệm thu: **29/10/2026**. Môi trường thực nghiệm mới là Lab Quân; dữ liệu Tuần 3 và minh chứng monitoring Khôi được dẫn chiếu theo đúng ngày và môi trường.

| Mã | Tiêu chí đối chiếu | Kết quả và tài liệu |
|---|---|---|
| W4-01 | Kiểm kê tài nguyên và source triển khai | Đối chiếu API, queue, mapping, Lambda và Orders; [inventory nghiệm thu](week4-report.md) |
| W4-02 | Luồng từ API tới cơ sở dữ liệu | Producer đúng source tham chiếu, mapping Enabled; HTTP 202 và đúng orderId PROCESSED; [E2E](week4-report.md) |
| W4-03 | Validation và bảo vệ dữ liệu | 13/13 HTTP đúng kỳ vọng, replay/conflict giữ item, năm lần lỗi và tương quan DLQ; [ma trận kiểm thử](week4-report.md) |
| W4-04 | Giám sát và phân phối cảnh báo | Logs/metrics Quân và manual Alarm → SNS → email Khôi; phân biệt với metric-driven alert; [phạm vi minh chứng](evidence/week4/README.md) |
| W4-05 | Phân tích hiệu năng có căn cứ | B1/B2/B3 giữ đúng điều kiện và giới hạn mẫu; [đánh giá](final-report.md) |
| W4-06 | Đánh giá chi phí | Sáu yếu tố dịch vụ và nguồn giá chính thức; [phân tích chi phí](week4-cost-analysis.md) |
| W4-07 | Quản lý tài nguyên và minh chứng | Giữ tài nguyên đối soát, không purge/delete; [trạng thái cuối](week4-report.md) |
| W4-08 | Hồi quy và tính nhất quán source | 56 tests/114 subtests, unittest 56, compile/lint và bảy CLI checks; [kết quả offline](evidence/week4/offline-validation.md) |
| W4-09 | Tổng hợp học thuật | [Báo cáo cuối kỳ](final-report.md), [traceability](traceability.md), [kịch bản demo](demo-script.md) và [khai báo AI](ai-declaration.md) |

Kết quả chỉ áp dụng phạm vi thử nghiệm đã mô tả. Bằng chứng DLQ là tương quan cấu hình/log/số lượng; monitoring Khôi là phép thử phân phối cảnh báo thủ công. Không suy thành kiểm chứng body DLQ, cảnh báo metric-driven mới hoặc năng lực production.
