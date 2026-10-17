# Chỉ mục minh chứng Tuần 1

## 1. Phạm vi

Tuần 1 có **hai PoC độc lập**:
- Quân: SQS/DLQ/Consumer.
- Khôi: DynamoDB/Producer/API/SNS.

Không dùng evidence Tuần 1 để tuyên bố Full E2E.

## 2. Quân — `sv1`

Thư mục:

```text
docs/evidence/week1/sv1/
screenshots/week1/sv1/
```

Các nhóm ảnh:
- AWS Console/LabRole.
- SQS main queue.
- DLQ.
- Redrive.
- Consumer Lambda.
- Trigger enable/disable.
- Direct valid/invalid Lambda test.
- SQS send/receive.
- Consumer success log.
- Retry/error log.
- Message tới DLQ và body.

Tổng file ảnh hiện có ở `sv1`: 26.

## 3. Khôi — `sv2`

Thư mục:

```text
docs/evidence/week1/sv2/
screenshots/week1/sv2/
```

6 ảnh chính:

1. `01-dynamodb-orders.png`
2. `02-lambda-producer-202.png`
3. `03-api-route-post-orders.png`
4. `04-api-powershell-202.png`
5. `05-sns-topic.png`
6. `06-sns-email-confirmed.png`

## 4. Kết luận evidence Tuần 1

- SQS/DLQ/Consumer PoC: có evidence.
- API/Producer/DynamoDB/SNS PoC: có evidence.
- Full E2E: chưa thuộc Tuần 1.
