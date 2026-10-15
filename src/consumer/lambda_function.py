"""SV1 Quan SQS Consumer Lambda - Week 2 DynamoDB Integration and Idempotency.

Minimal AWS Lambda function for validating and processing orders received via
Amazon SQS Event Source Mapping and persisting them into DynamoDB with atomic
conditional put and strongly consistent duplicate verification.
Console-pasteable, safe bounded structured logging.
"""

import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("consumer")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

# Fixed safe error codes
ERR_MALFORMED_EVENT = "MALFORMED_EVENT"
ERR_MALFORMED_RECORD = "MALFORMED_RECORD"
ERR_INVALID_JSON = "INVALID_JSON"
ERR_INVALID_SCHEMA = "INVALID_SCHEMA"
ERR_INTERNAL_ERROR = "INTERNAL_ERROR"
ERR_CONFIG_ERROR = "CONFIG_ERROR"
ERR_ORDER_CONFLICT = "ORDER_CONFLICT"
ERR_ITEM_NOT_FOUND = "ITEM_NOT_FOUND"


class ConsumerError(Exception):
    """Safe fixed-code consumer exception containing no payload or sensitive context."""

    def __init__(self, error_code: str) -> None:
        super().__init__(error_code)
        self.error_code = error_code


def _sanitize_identifier(value: Any, max_length: int = 128) -> str:
    """Sanitize and bound identifiers for safe structured logging.

    Prevents CRLF log injection and bounds identifier length.
    """
    if not isinstance(value, str):
        return ""
    truncated = value[:max_length]
    cleaned = []
    for ch in truncated:
        if ch.isprintable() and ch not in ("\r", "\n", "\t"):
            cleaned.append(ch)
        else:
            cleaned.append(f"\\x{ord(ch):02x}")
    return "".join(cleaned)


def _log_success(order_id: str, message_id: str, status: str = "PROCESSED") -> None:
    """Log processing success with bounded safe identifiers and clear status marker."""
    safe_order_id = _sanitize_identifier(order_id)
    safe_message_id = _sanitize_identifier(message_id)
    log_entry = {
        "level": "INFO",
        "status": status,
        "messageId": safe_message_id,
        "orderId": safe_order_id,
    }
    logger.info(json.dumps(log_entry))


def _log_error(error_code: str, message_id: str) -> None:
    """Log failure with safe fixed code only; never payload, body, customer, or product data."""
    safe_message_id = _sanitize_identifier(message_id)
    log_entry = {
        "level": "ERROR",
        "errorCode": error_code,
        "messageId": safe_message_id,
    }
    logger.error(json.dumps(log_entry))


def _is_valid_str(val: Any) -> bool:
    """Check if value is a non-empty string and not a boolean."""
    return isinstance(val, str) and not isinstance(val, bool) and bool(val.strip())


def _validate_order_payload(data: Any, safe_msg_id: str) -> Dict[str, Any]:
    """Validate JSON payload against Week 2 flat message schema.

    Schema:
    - Root: JSON object
    - orderId: non-empty string, whitespace-only fails, not bool
    - customerId: non-empty string, whitespace-only fails, not bool
    - productId: non-empty string, whitespace-only fails, not bool
    - quantity: positive integer >= 1, excluding bool, float, strings, zero, negatives
    - status: non-empty string, whitespace-only fails, not bool
    - createdAt: non-empty string, whitespace-only fails, not bool
    - Extra fields allowed (no unspecified rejection).
    """
    if not isinstance(data, dict):
        _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
        raise ConsumerError(ERR_INVALID_SCHEMA)

    if (
        not _is_valid_str(data.get("orderId"))
        or not _is_valid_str(data.get("customerId"))
        or not _is_valid_str(data.get("productId"))
        or not _is_valid_str(data.get("status"))
        or not _is_valid_str(data.get("createdAt"))
    ):
        _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
        raise ConsumerError(ERR_INVALID_SCHEMA)

    quantity = data.get("quantity")
    if type(quantity) is not int or quantity <= 0:
        _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
        raise ConsumerError(ERR_INVALID_SCHEMA)

    return data


def _get_table() -> Any:
    """Get DynamoDB Table resource using TABLE_NAME environment variable."""
    table_name = os.environ.get("TABLE_NAME")
    if not table_name or not table_name.strip():
        _log_error(ERR_CONFIG_ERROR, "UNKNOWN")
        raise ConsumerError(ERR_CONFIG_ERROR)
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


def lambda_handler(event: Any, context: Any = None) -> Dict[str, Any]:
    """AWS Lambda entry point for SQS consumer with DynamoDB idempotency.

    Processes SQS records with atomic conditional write and strongly consistent
    duplicate check on conflict. Raises on any failure to preserve SQS full-batch
    retry semantics.
    """
    if not isinstance(event, dict) or "Records" not in event:
        _log_error(ERR_MALFORMED_EVENT, "UNKNOWN")
        raise ConsumerError(ERR_MALFORMED_EVENT)

    records = event.get("Records")
    if not isinstance(records, list) or len(records) == 0:
        _log_error(ERR_MALFORMED_EVENT, "UNKNOWN")
        raise ConsumerError(ERR_MALFORMED_EVENT)

    table = _get_table()

    processed_count = 0

    for record in records:
        if not isinstance(record, dict) or "body" not in record:
            _log_error(ERR_MALFORMED_RECORD, "UNKNOWN")
            raise ConsumerError(ERR_MALFORMED_RECORD)

        raw_msg_id = record.get("messageId", "UNKNOWN")
        safe_msg_id = _sanitize_identifier(raw_msg_id)

        raw_body = record.get("body")
        if not isinstance(raw_body, str):
            _log_error(ERR_MALFORMED_RECORD, safe_msg_id)
            raise ConsumerError(ERR_MALFORMED_RECORD)

        try:
            data = json.loads(raw_body)
        except Exception:
            _log_error(ERR_INVALID_JSON, safe_msg_id)
            raise ConsumerError(ERR_INVALID_JSON) from None

        try:
            validated = _validate_order_payload(data, safe_msg_id)
        except ConsumerError:
            raise
        except Exception:
            _log_error(ERR_INTERNAL_ERROR, safe_msg_id)
            raise ConsumerError(ERR_INTERNAL_ERROR) from None

        order_id = validated["orderId"]
        item_to_put = dict(validated)
        item_to_put["status"] = "PROCESSED"

        try:
            table.put_item(
                Item=item_to_put,
                ConditionExpression="attribute_not_exists(orderId)",
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code != "ConditionalCheckFailedException":
                _log_error(ERR_INTERNAL_ERROR, safe_msg_id)
                raise

            # ConditionalCheckFailedException: orderId already exists
            try:
                get_res = table.get_item(Key={"orderId": order_id}, ConsistentRead=True)
            except Exception:
                _log_error(ERR_INTERNAL_ERROR, safe_msg_id)
                raise

            existing_item = get_res.get("Item")
            if not existing_item:
                _log_error(ERR_ITEM_NOT_FOUND, safe_msg_id)
                raise ConsumerError(ERR_ITEM_NOT_FOUND)

            # Compare stable business fields: customerId, productId, quantity, createdAt
            is_identical = (
                existing_item.get("customerId") == validated.get("customerId")
                and existing_item.get("productId") == validated.get("productId")
                and not isinstance(existing_item.get("quantity"), bool)
                and existing_item.get("quantity") == validated.get("quantity")
                and existing_item.get("createdAt") == validated.get("createdAt")
            )

            if not is_identical:
                _log_error(ERR_ORDER_CONFLICT, safe_msg_id)
                raise ConsumerError(ERR_ORDER_CONFLICT)
        except ConsumerError:
            raise
        except Exception:
            _log_error(ERR_INTERNAL_ERROR, safe_msg_id)
            raise

        _log_success(order_id, safe_msg_id, "PROCESSED")
        processed_count += 1

    # ponytail: SQS full-batch failure semantics without ReportBatchItemFailures per Week 2 contract.
    # Upgrade path: enable ReportBatchItemFailures and return batchItemFailures in Week 3/4 if needed.
    return {
        "statusCode": 200,
        "status": "PROCESSED",
        "processedCount": processed_count,
    }
