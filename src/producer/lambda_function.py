
import json
import uuid
import os
import boto3
from datetime import datetime, timezone

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["QUEUE_URL"]


def lambda_handler(event, context):
    try:
        body = {}

        if event.get("body"):
            body = json.loads(event["body"])

        order_id = str(uuid.uuid4())

        order = {
            "orderId": order_id,
            "customerId": body.get("customerId", "UNKNOWN"),
            "productId": body.get("productId", "UNKNOWN"),
            "quantity": body.get("quantity", 1),
            "status": "PENDING",
            "createdAt": datetime.now(timezone.utc).isoformat()
        }

        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(order)
        )

        print("ORDER_SENT_TO_SQS")
        print(json.dumps(order))

        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Order accepted",
                "order": order
            })
        }

    except Exception as e:
        print("ERROR:", str(e))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Internal server error"
            })
        }
