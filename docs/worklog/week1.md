# Nhật ký hoạt động Tuần 1

Mỗi sinh viên phải ghi ít nhất **8 giờ thực tế/tuần**. Khôi tổng hợp báo cáo tiến độ riêng; Quan chỉ cung cấp và xác nhận phần việc của mình. Không tính timestamp log/ảnh hoặc thời gian AI thực thi thành giờ làm.

## 1. SV1 — Quan

| Ngày ghi nhận | Bắt đầu | Kết thúc | Hoạt động | Số giờ | Minh chứng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-11 | Chờ bổ sung | Chờ bổ sung | Cấu hình SQS Standard `orders-queue`, `orders-dlq`, Consumer `order-processor` và trigger | | [W1-Q-CONFIG](../evidence/week1/README.md#w1-q-config) |
| 2026-10-11 | Chờ bổ sung | Chờ bổ sung | Test Lambda trực tiếp: valid thành công; quantity sai sinh `INVALID_SCHEMA` | | [W1-Q-DIRECT](../evidence/week1/README.md#w1-q-direct) |
| 2026-10-11 | Chờ bổ sung | Chờ bổ sung | Qua SQS: `ORD-W1-Q-003` có `POC_VALIDATED`; `ORD-W1-Q-ERR-002` có lỗi lặp và body trong DLQ | | [W1-Q-E2E](../evidence/week1/README.md#w1-q-e2e) |

Ngày trên lấy theo minh chứng AWS; Quan cần xác nhận ngày thực hiện, người thực hiện và thời lượng trước khi tính giờ.

- **Tổng giờ thực tế**: `_____` — chưa xác minh.
- **Đạt ≥ 8 giờ**: [ ] Đã đạt / [ ] Chưa đạt.

[Sơ đồ Mermaid](../architecture/README.md) đã được thêm vào repo trong lần cập nhật tài liệu này; chưa ghi giờ làm hoặc coi đó là phê duyệt của sinh viên.

## 2. SV2 — Khôi

Hoạt động và giờ làm SV2 do Khôi ghi trong báo cáo riêng; repo chưa có dữ liệu để đối soát tổng giờ hoặc xác nhận đạt 8 giờ. Không suy diễn hoạt động SV2 từ kết quả SV1.
