
"""SV1 Quan SQS Consumer Lambda PoC.

Minimal AWS Lambda function (Python 3.13 standard library only) for validating
and processing orders received via Amazon SQS Event Source Mapping.
Console-pasteable, no external dependencies.
"""

import json
import logging
from typing import Any, Dict

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


def _log_success(order_id: str, message_id: str, item_count: int) -> None:
    """Log validation success with bounded safe identifiers and clear POC_VALIDATED marker."""
    safe_order_id = _sanitize_identifier(order_id)
    safe_message_id = _sanitize_identifier(message_id)
    log_entry = {
        "level": "INFO",
        "status": "POC_VALIDATED",
        "messageId": safe_message_id,
        "orderId": safe_order_id,
        "itemCount": item_count,
    }
    logger.info(json.dumps(log_entry))


def _log_error(error_code: str, message_id: str) -> None:
    """Log validation failure with safe fixed code only; never payload, body, or items."""
    safe_message_id = _sanitize_identifier(message_id)
    log_entry = {
        "level": "ERROR",
        "errorCode": error_code,
        "messageId": safe_message_id,
    }
    logger.error(json.dumps(log_entry))


def _validate_order_payload(data: Any, safe_msg_id: str) -> Dict[str, Any]:
    """Validate JSON payload against integration contract schema.

    Contract:
    - Root: JSON object
    - orderId: non-empty string, whitespace-only fails
    - items: non-empty list of objects
    - each item: sku (non-empty string, whitespace-only fails),
                 quantity (positive int >= 1, excluding bool)
    - Extra fields allowed (no unspecified rejection).
    """
    if not isinstance(data, dict):
        _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
        raise ConsumerError(ERR_INVALID_SCHEMA)

    order_id = data.get("orderId")
    if (
        not isinstance(order_id, str)
        or isinstance(order_id, bool)
        or not order_id.strip()
    ):
        _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
        raise ConsumerError(ERR_INVALID_SCHEMA)

    items = data.get("items")
    if not isinstance(items, list) or len(items) == 0:
        _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
        raise ConsumerError(ERR_INVALID_SCHEMA)

    for item in items:
        if not isinstance(item, dict):
            _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
            raise ConsumerError(ERR_INVALID_SCHEMA)

        sku = item.get("sku")
        if not isinstance(sku, str) or isinstance(sku, bool) or not sku.strip():
            _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
            raise ConsumerError(ERR_INVALID_SCHEMA)

        quantity = item.get("quantity")
        # In Python, bool is a subclass of int (isinstance(True, int) is True).
        # We explicitly check type(quantity) is int to reject bool, float, etc.
        if type(quantity) is not int or quantity <= 0:
            _log_error(ERR_INVALID_SCHEMA, safe_msg_id)
            raise ConsumerError(ERR_INVALID_SCHEMA)

    return data


def lambda_handler(event: Any, context: Any = None) -> Dict[str, Any]:
    """AWS Lambda entry point for SQS consumer PoC.

    Processes all SQS Records in the event.
    On success, logs POC_VALIDATED for each record.
    On failure (invalid JSON/schema/record/event), logs fixed error code and raises
    ConsumerError uncaught to trigger SQS full-batch retry/DLQ routing.

    Note: PoC validation only, no DynamoDB write/idempotency.
    Upgrade path: DynamoDB conditional PutItem and idempotency read in Week 2.

    Note: Whole-batch failure without ReportBatchItemFailures.
    Upgrade path: SQS batchItemFailures with batch size > 1 in Week 2.
    """
    if not isinstance(event, dict) or "Records" not in event:
        _log_error(ERR_MALFORMED_EVENT, "UNKNOWN")
        raise ConsumerError(ERR_MALFORMED_EVENT)

    records = event.get("Records")
    if not isinstance(records, list) or len(records) == 0:
        _log_error(ERR_MALFORMED_EVENT, "UNKNOWN")
        raise ConsumerError(ERR_MALFORMED_EVENT)

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
            # Suppress chained exception to avoid leaking payload or decode internals
            raise ConsumerError(ERR_INVALID_JSON) from None

        try:
            validated = _validate_order_payload(data, safe_msg_id)
        except ConsumerError:
            raise
        except Exception:
            _log_error(ERR_INTERNAL_ERROR, safe_msg_id)
            raise ConsumerError(ERR_INTERNAL_ERROR) from None

        _log_success(validated["orderId"], safe_msg_id, len(validated["items"]))
        processed_count += 1

    return {
        "statusCode": 200,
        "status": "POC_VALIDATED",
        "processedCount": processed_count,
    }
