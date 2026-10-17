"""AWS Lambda Producer: validate requests before accepting an order into SQS."""

import json
import os
import uuid
from datetime import datetime, timezone

import boto3

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["QUEUE_URL"]


def _response(status, message, order=None):
    payload = {"message": message}
    if order is not None:
        payload["order"] = order
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _validate(event):
    if not isinstance(event, dict):
        return None, "Invalid request"
    raw_body = event.get("body")
    if not isinstance(raw_body, str) or not raw_body.strip():
        return None, "Invalid JSON body"
    try:
        body = json.loads(raw_body)
    except (ValueError, TypeError):
        return None, "Invalid JSON body"
    if not isinstance(body, dict):
        return None, "JSON body must be an object"
    for field in ("customerId", "productId"):
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"{field} is required"
    quantity = body.get("quantity")
    if type(quantity) is not int or quantity <= 0:
        return None, "quantity must be a positive integer"
    return body, None


def lambda_handler(event, context):
    body, error = _validate(event)
    if error:
        return _response(400, error)

    order = {
        "orderId": str(uuid.uuid4()),
        "customerId": body["customerId"],
        "productId": body["productId"],
        "quantity": body["quantity"],
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    try:
        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(order))
    except Exception:
        print("ERROR: SQS_SEND_FAILED")
        return _response(500, "Internal server error")

    print("ORDER_SENT_TO_SQS")
    print(json.dumps({"orderId": order["orderId"], "status": order["status"]}))
    return _response(202, "Order accepted", order)
