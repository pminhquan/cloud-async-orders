# cloud-async-orders

Đề tài Cloud: **Hàng đợi xử lý đơn hàng bất đồng bộ với SQS, DLQ và Lambda**.

Mục tiêu của hệ thống là tách Producer và Consumer bằng Amazon SQS, xử lý lỗi qua DLQ, lưu kết quả vào DynamoDB và giám sát/cảnh báo bằng CloudWatch + SNS.

## Kiến trúc đích

```text
Client
  ↓
API Gateway
  ↓
Producer Lambda
  ↓
SQS Standard/FIFO
  ↓
Consumer Lambda
  ↓
DynamoDB

Message lỗi → DLQ → CloudWatch Alarm → SNS → Email
```

## Trạng thái Tuần 1

Tuần 1 tập trung **làm quen dịch vụ, thiết kế kiến trúc và dựng PoC riêng cho hai phía**, chưa coi là hệ thống E2E hoàn chỉnh.

- **Quân (SV1):** SQS/DLQ, Consumer Lambda, retry/DLQ PoC, nghiên cứu Standard/FIFO và sơ đồ kiến trúc.
- **Khôi (SV2):** API Gateway, Producer Lambda, DynamoDB, SNS Email Subscription và kiểm thử API `202`.
- Hai PoC được kiểm thử riêng. Việc tích hợp `Producer → SQS → Consumer → DynamoDB` chuyển sang Tuần 2.

Chi tiết:
- [Báo cáo Tuần 1](docs/week1-report.md)
- [Kế hoạch Tuần 1](docs/week1-plan.md)
- [Phân công](docs/task-assignment.md)
- [Sơ đồ kiến trúc](docs/architecture/README.md)
- [Danh mục AWS](docs/aws-inventory.md)
- [Hợp đồng tích hợp](docs/integration-contract.md)
- [Worklog](docs/worklog/week1.md)

## Cấu trúc repository

```text
cloud-async-orders/
├── src/
│   ├── producer/
│   └── consumer/
├── tests/
├── scripts/
│   └── test-order-api.ps1
├── docs/
│   ├── architecture/
│   ├── research/
│   ├── evidence/
│   ├── worklog/
│   ├── week1-report.md
│   └── ...
├── screenshots/
│   └── week1/
│       ├── sv1/
│       └── sv2/
├── iac/
│   └── README.md
└── README.md
```

Cách tổ chức này ưu tiên: **mã nguồn riêng, script test riêng, tài liệu riêng và ảnh minh chứng riêng** để dễ kiểm tra trên GitHub.

## Kiểm thử nhanh API PoC

Windows PowerShell:

```powershell
./scripts/test-order-api.ps1
```

Kết quả Tuần 1 mong đợi:

```text
HTTP Status: 202
```

Lưu ý: `202` ở PoC hiện tại chỉ chứng minh API Gateway → Producer Lambda hoạt động; chưa chứng minh message đã vào SQS.

## Region và quy ước

- Region: `us-east-1`
- IAM: dùng `LabRole` có sẵn, không tạo IAM User/Role mới.
- Tags dự kiến thống nhất:
  - `Project = AsyncOrderProcessing`
  - `Owner = Khoi-Quan`

## Bảo mật khi để repository Public

Không commit:
- AWS Access Key
- Secret Access Key
- Session Token
- Mật khẩu hoặc file credentials

Ảnh minh chứng có thể chứa Account ID hoặc email; nên kiểm tra lại thông tin cá nhân trước khi public repository.
