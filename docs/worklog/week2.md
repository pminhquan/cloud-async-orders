# Nhật ký hoạt động Tuần 2

Mỗi sinh viên phải ghi tối thiểu **8 giờ làm thực tế có tài liệu mỗi tuần** theo [yêu cầu dự án](../requirements.md). Khôi tổng hợp báo cáo tiến độ và khai báo AI; Quan cung cấp, xác nhận phần việc và việc sử dụng AI của mình.

Các bảng dưới ghi những hoạt động đã được cung cấp trong bàn giao Tuần 2. Chưa có ngày làm hoặc thời lượng thực tế, nên giữ `TODO`; không lấy ngày commit, timestamp log/ảnh, thời gian AI chạy hoặc thời lượng dự kiến thay cho giờ làm. Kết quả local đã có không phải kết quả AWS. Không chạy lại tests hay AWS trong tác vụ biên tập tài liệu này.

## 1. SV1 — Quan

| Mã việc | Hoạt động | Ngày thực tế | Thời gian thực tế | Kết quả đã biết | Minh chứng / phần còn thiếu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| W2-03 | Nâng cấp Consumer theo schema phẳng; tích hợp DynamoDB, idempotency và log an toàn | TODO | TODO | Hoàn thành local trên `feat/week2-consumer-dynamodb`, commit `0192d2b`. Theo bàn giao, PR #5 đang mở, chưa merge; chưa triển khai AWS. | [Mã Consumer tại commit](https://github.com/pminhquan/cloud-async-orders/blob/0192d2b554cf9795e21eb1b0b20dba8c4102c243/src/consumer/lambda_function.py), [PR #5](https://github.com/pminhquan/cloud-async-orders/pull/5). |
| W2-03, W2-06, W2-08 | Kiểm tra local: validation, duplicate/conflict, lỗi DB, nhiều record và replay | TODO | TODO | Kết quả local đã bàn giao: 15/15 unit tests qua; lời gọi DynamoDB được mock, không cần AWS hoặc credentials thật. Không coi đây là kiểm thử E2E hoặc xác nhận triển khai. | [Tests tại commit](https://github.com/pminhquan/cloud-async-orders/blob/0192d2b554cf9795e21eb1b0b20dba8c4102c243/tests/test_consumer.py). TODO: bổ sung liên kết log kiểm thử local vào bộ minh chứng nhóm. |

Link tới commit được dùng để phân biệt mã Tuần 2 chưa merge với mã PoC đang có trên `main`.

## 2. SV2 — Khôi

| Mã việc | Hoạt động | Ngày thực tế | Thời gian thực tế | Kết quả đã biết | Minh chứng / phần còn thiếu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| W2-02, W2-04 | Thiết lập tài nguyên và cấu hình Lab tích hợp | TODO | TODO | Khôi tự báo cáo đã có API, Producer, SQS/DLQ, Consumer, DynamoDB, SNS; đã đặt `QUEUE_URL`, `TABLE_NAME=Orders` và trigger. Chưa đối chiếu độc lập trên AWS. | [Danh mục cấu hình được báo cáo](../integration-contract.md). TODO: liên kết minh chứng cấu hình và đúng phiên bản mã; không suy ra đã triển khai Consumer của Quan. |
| W2-02 | Kiểm thử riêng Producer → SQS | TODO | TODO | Khôi báo cáo thành công. Producer tạo `orderId=3435e200-ccd1-4664-90a8-633553d55188`; chưa xác nhận được cùng UUID ở log Consumer hoặc DynamoDB. | TODO: liên kết phản hồi API, kết quả `SendMessage` và dấu vết tin nhắn; E2E vẫn chưa được xác minh. |
| W2-04 | Kiểm thử riêng SQS → Consumer → DynamoDB với bản Consumer đang triển khai | TODO | TODO | Khôi báo cáo thành công; chưa xác minh độc lập. Kết quả này không chứng minh mã conditional-write/idempotency của Quan đã chạy trên AWS. | TODO: liên kết log Consumer, item DynamoDB và phiên bản Consumer đã dùng. |

## 3. Hoạt động chung và việc chưa hoàn thành

| Mã việc | Hoạt động | Ngày thực tế | Thời gian thực tế của mỗi người | Kết quả đã biết | Minh chứng / phần còn thiếu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| W2-01 | Thống nhất hợp đồng dữ liệu và Lab tích hợp | TODO | Quan: TODO; Khôi: TODO | Theo thông tin nhóm, dùng schema phẳng và Lab của Khôi tại `us-east-1`; Khôi triển khai AWS. | [Hợp đồng](../integration-contract.md), [kế hoạch](../week2-plan.md). Không suy ra ngày họp, thời lượng hoặc biên bản họp từ thông tin này. |

Các việc sau vẫn là kế hoạch/chờ thực thi, chưa được ghi thành hoạt động hoàn thành hoặc giờ làm:

- W2-04: tích hợp và triển khai bản Consumer của Quan được nhóm chấp thuận.
- W2-05–W2-08: E2E, duplicate/conflict, retry/DLQ và batch trên AWS với minh chứng đối chiếu.
- W2-09–W2-10: tải nhỏ có giới hạn và hoàn thiện bộ minh chứng Tuần 2.
- W2-11–W2-12: bổ sung nhật ký thực tế, tổng hợp báo cáo tuần và khai báo AI; việc nộp chưa xác nhận.

## 4. Đối soát giờ làm và báo cáo

| Sinh viên | Tổng giờ thực tế đã cung cấp | Đạt ≥ 8 giờ thực tế có tài liệu? | Thông tin còn phải bổ sung |
| :--- | :--- | :--- | :--- |
| Quan | TODO — chưa có tổng giờ để cộng | Chưa xác nhận | Ngày làm, thời lượng từng hoạt động, kết quả và minh chứng; tự xác nhận phần SV1/AI. |
| Khôi | TODO — chưa có tổng giờ để cộng | Chưa xác nhận | Ngày làm, thời lượng từng hoạt động, kết quả và minh chứng; tổng hợp riêng báo cáo tuần/AI. |

Chỉ cộng giờ khi có ghi nhận thực tế của từng người; cùng tham gia một hoạt động không có nghĩa hai người có cùng thời lượng. Việc đã đạt giờ hoặc được duyệt Tuần 1 không chứng minh đã đạt giờ Tuần 2. Chưa có xác nhận Tuần 2 đã được nộp hoặc được giảng viên duyệt.
