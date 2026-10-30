# Kiến trúc hệ thống

## 1. Kiến trúc đích

```mermaid
flowchart LR
    Client[Client]
    API[API Gateway\norder-api]
    Producer[Lambda\norder-producer]
    Queue[SQS\norders-queue]
    Consumer[Lambda\norder-consumer]
    DB[(DynamoDB\nOrders)]
    DLQ[SQS DLQ\norders-dlq]
    Alarm[CloudWatch Alarm\ngiai đoạn sau]
    SNS[SNS\norder-dlq-alert]

    Client --> API --> Producer --> Queue --> Consumer --> DB
    Queue -->|failed receives| DLQ
    DLQ -.-> Alarm -.-> SNS
```

---

## 2. Tuần 1 — PoC độc lập

```mermaid
flowchart LR
    API[API Gateway] --> Producer[Producer PoC\nHTTP 202]
    Queue[SQS] --> Consumer[Consumer PoC\nvalidate/log]
    Queue --> DLQ[DLQ]
    DB[(DynamoDB Orders)]

    Producer -. chưa gửi SQS .-> Queue
    Consumer -. chưa ghi DB .-> DB
```

Đặc điểm:
- Khôi kiểm thử API/Producer riêng.
- Quân kiểm thử SQS/Consumer/DLQ riêng.
- Chưa dùng Full E2E làm kết luận Tuần 1.

---

## 3. Tuần 2 — luồng tích hợp

```mermaid
flowchart LR
    API[POST /orders]
    P[order-producer]
    Q[orders-queue]
    C[order-consumer]
    DB[(Orders)]
    D[orders-dlq]

    API -->|valid 202| P -->|SendMessage| Q --> C -->|PutItem PROCESSED| DB
    API -->|invalid 400| Reject[Reject request]
    Q -->|retry on failure| C
    Q -->|max receives exceeded| D
```

Đã kiểm thử trên Lab Quân:
- Full E2E.
- Idempotency.
- ORDER_CONFLICT.
- Invalid JSON → Retry → DLQ.
- Direct batch/replay.
- Small load test.

Đã kiểm thử trên Lab Khôi:
- Producer valid `202`.
- Producer invalid `400`.
- Invalid request không làm tăng queue.

---

## 4. Idempotency

```mermaid
flowchart TD
    M[SQS message] --> W[Conditional PutItem\nattribute_not_exists orderId]
    W -->|Success| Done[PROCESSED]
    W -->|orderId exists| Read[Consistent GetItem]
    Read --> Compare{Business fields identical?}
    Compare -->|Yes| Duplicate[Idempotent success\nno overwrite]
    Compare -->|No| Conflict[ORDER_CONFLICT\nfail invocation]
```

---

## 5. Phạm vi chưa hoàn tất tính đến Tuần 2

- CloudWatch Alarm → SNS alert hoàn chỉnh.
- Benchmark Standard vs FIFO chính thức.
- IaC production-like.
- Stress/load test lớn.

Các phần này được triển khai một phần ở Tuần 3 và nghiệm thu ở Tuần 4.

## 6. Trạng thái đến Tuần 4

Pipeline `API Gateway → Producer → SQS → Consumer → DynamoDB` được nghiệm thu trên Lab Quân ngày 29/10/2026. Template monitoring đã lint nhưng chưa triển khai trên Lab Quân; chuỗi Alarm → SNS → email chỉ có minh chứng thủ công trên Lab Khôi ngày 24/10/2026. Chi tiết và giới hạn: [báo cáo Tuần 4](../week4-report.md).
