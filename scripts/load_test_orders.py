"""Week 3 Controlled Load Test & DynamoDB E2E Reconciliation Tool (W3-03).

Safe, bounded API load test and read-only DynamoDB GetItem reconciliation tool.
Distinguishes HTTP 202 (Producer accepted & enqueued to SQS) from DynamoDB
status == PROCESSED (Consumer completed persistence).
"""

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import socket
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import urllib.error
from urllib.parse import urlparse
import urllib.request
import uuid

PREFIX_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,40}$")
TABLE_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")


class LoadTestError(Exception):
    """Safe validation or execution error for controlled load testing."""


def sanitize_text(value: Any, max_length: int = 160) -> str:
    if not isinstance(value, str):
        value = str(value)
    cleaned = "".join(
        ch if (ch.isprintable() and ch not in ("\r", "\n", "\t")) else " "
        for ch in value
    ).strip()
    cleaned = re.sub(r"AKIA[0-9A-Z]{16}", "[REDACTED_KEY]", cleaned)
    cleaned = re.sub(r"ASIA[0-9A-Z]{16}", "[REDACTED_KEY]", cleaned)
    cleaned = re.sub(r"\b[0-9]{12}\b", "[REDACTED_ACCOUNT]", cleaned)
    return cleaned[:max_length]


def compute_latency_stats(values_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    clean = sorted(float(v) for v in values_ms if v is not None and math.isfinite(float(v)))
    n = len(clean)
    if n == 0:
        return {
            "count": 0,
            "minMs": None,
            "maxMs": None,
            "meanMs": None,
            "medianMs": None,
            "p95Ms": None,
        }
    mid = n // 2
    median = clean[mid] if n % 2 == 1 else (clean[mid - 1] + clean[mid]) / 2.0
    p95_idx = max(0, min(n - 1, math.ceil(0.95 * n) - 1))
    return {
        "count": n,
        "minMs": round(clean[0], 3),
        "maxMs": round(clean[-1], 3),
        "meanMs": round(sum(clean) / n, 3),
        "medianMs": round(median, 3),
        "p95Ms": round(clean[p95_idx], 3),
    }


def validate_endpoint(endpoint: str) -> str:
    """Validate API endpoint URL; never falls back to a hard-coded URL."""
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise LoadTestError("API endpoint is required (no hard-coded fallback endpoint is used).")
    raw = endpoint.strip()
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.netloc:
        raise LoadTestError("API endpoint must be a valid https:// URL.")
    if any(ch.isspace() for ch in raw):
        raise LoadTestError("API endpoint must not contain whitespace.")
    return raw


def validate_load_test_config(
    *,
    endpoint: str,
    request_count: int,
    rate_limit: float,
    timeout_seconds: float,
    customer_prefix: str,
    table_name: str,
    reconcile_timeout: float,
    reconcile_max_polls: int,
    dry_run: bool = False,
    execute: bool = False,
    confirm_target: Optional[str] = None,
) -> Tuple[str, str]:
    """Validate bounded load test parameters respecting AWS Learner Lab limits."""
    if dry_run and execute:
        raise LoadTestError("Conflicting flags: --dry-run and --execute cannot be used together.")

    clean_endpoint = validate_endpoint(endpoint)
    parsed = urlparse(clean_endpoint)
    host = parsed.netloc

    if type(request_count) is not int or request_count < 1 or request_count > 100:
        raise LoadTestError("request_count must be an integer between 1 and 100 (bounded load test).")
    if (
        isinstance(rate_limit, bool)
        or not isinstance(rate_limit, (int, float))
        or not math.isfinite(float(rate_limit))
        or float(rate_limit) <= 0.0
        or float(rate_limit) > 10.0
    ):
        raise LoadTestError(
            "rate_limit must be a finite number > 0 and <= 10.0 req/sec to respect Learner Lab concurrency <= 10."
        )
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or float(timeout_seconds) <= 0.0
        or float(timeout_seconds) > 30.0
    ):
        raise LoadTestError("timeout_seconds must be a finite number > 0 and <= 30.0 seconds.")
    if not isinstance(customer_prefix, str) or not PREFIX_PATTERN.match(customer_prefix.strip()):
        raise LoadTestError("customer_prefix must be 1..40 alphanumeric/dash/underscore characters.")
    if not isinstance(table_name, str) or not TABLE_PATTERN.match(table_name.strip()):
        raise LoadTestError("Invalid DynamoDB table_name.")
    if (
        isinstance(reconcile_timeout, bool)
        or not isinstance(reconcile_timeout, (int, float))
        or not math.isfinite(float(reconcile_timeout))
        or float(reconcile_timeout) <= 0.0
        or float(reconcile_timeout) > 120.0
    ):
        raise LoadTestError("reconcile_timeout must be a finite number > 0 and <= 120.0 seconds.")
    if type(reconcile_max_polls) is not int or reconcile_max_polls < 1 or reconcile_max_polls > 20:
        raise LoadTestError("reconcile_max_polls must be an integer between 1 and 20.")

    if execute:
        if not confirm_target or confirm_target.strip() not in (clean_endpoint, host):
            raise LoadTestError(
                f"Live execution requires --confirm-target matching the endpoint host '{host}' or full URL."
            )

    return clean_endpoint, host


def default_http_post(url: str, payload: Dict[str, Any], timeout_seconds: float) -> Tuple[int, str]:
    """Send HTTP POST JSON request using Python standard library urllib."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status_code = int(getattr(resp, "status", resp.getcode()))
            body_text = resp.read().decode("utf-8", errors="replace")
            return status_code, body_text
    except urllib.error.HTTPError as http_err:
        body_text = ""
        try:
            body_text = http_err.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return int(http_err.code), body_text


def build_bounded_boto_config(timeout_seconds: float) -> Any:
    """Build a botocore Config with single-attempt execution (no hidden retries) and per-call socket timeouts bounded by timeout_seconds."""
    from botocore.config import Config  # type: ignore

    budget = max(0.05, float(timeout_seconds))
    per_call_timeout = min(5.0, budget)
    return Config(
        connect_timeout=per_call_timeout,
        read_timeout=per_call_timeout,
        retries={"total_max_attempts": 1, "max_attempts": 0, "mode": "standard"},
    )


def reconcile_orders_dynamodb(
    *,
    order_ids: Sequence[str],
    table_name: str = "Orders",
    region: str = "us-east-1",
    timeout_seconds: float = 30.0,
    max_polls: int = 6,
    initial_backoff_seconds: float = 0.5,
    dynamodb_table: Any = None,
    clock_fn: Callable[[], float] = time.perf_counter,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    """Reconcile collected orderIds via read-only DynamoDB GetItem (never Scan or write)."""
    unique_ids = list(dict.fromkeys(oid for oid in order_ids if isinstance(oid, str) and oid.strip()))
    if not unique_ids:
        return {
            "verificationStatus": "NO_ORDER_IDS_TO_VERIFY",
            "tableName": table_name,
            "orderIdsRequested": 0,
            "processedCount": 0,
            "pendingOrOtherStatusCount": 0,
            "notFoundCount": 0,
            "unverifiedCount": 0,
            "pollsExecuted": 0,
            "reconciliationDurationSeconds": 0.0,
            "perOrder": {},
            "errorCode": None,
        }

    if dynamodb_table is None:
        try:
            import boto3  # type: ignore
        except ModuleNotFoundError:
            return {
                "verificationStatus": "UNVERIFIED_MISSING_BOTO3",
                "tableName": table_name,
                "orderIdsRequested": len(unique_ids),
                "processedCount": 0,
                "pendingOrOtherStatusCount": 0,
                "notFoundCount": 0,
                "unverifiedCount": len(unique_ids),
                "pollsExecuted": 0,
                "reconciliationDurationSeconds": 0.0,
                "perOrder": {oid: {"state": "UNVERIFIED", "dbStatus": None} for oid in unique_ids},
                "errorCode": "MISSING_BOTO3",
            }
        boto_cfg = build_bounded_boto_config(timeout_seconds)
        dynamodb_res = boto3.resource("dynamodb", region_name=region, config=boto_cfg)
        dynamodb_table = dynamodb_res.Table(table_name)

    start_t = clock_fn()
    deadline = start_t + float(timeout_seconds)
    per_order: Dict[str, Dict[str, Any]] = {
        oid: {"state": "PENDING_LOOKUP", "dbStatus": None, "attempts": 0} for oid in unique_ids
    }
    remaining = set(unique_ids)
    polls_executed = 0
    backoff = max(0.05, initial_backoff_seconds)

    while remaining and polls_executed < max_polls and clock_fn() < deadline:
        polls_executed += 1
        for oid in [o for o in unique_ids if o in remaining]:
            if clock_fn() >= deadline:
                break
            per_order[oid]["attempts"] += 1
            try:
                resp = dynamodb_table.get_item(Key={"orderId": oid}, ConsistentRead=True)
            except Exception as exc:
                err_code = (
                    getattr(exc, "response", {}).get("Error", {}).get("Code")
                    if hasattr(exc, "response")
                    else None
                )
                safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
                if safe_code in ("AccessDeniedException", "UnauthorizedOperation", "UnrecognizedClientException"):
                    elapsed = round(max(0.0, clock_fn() - start_t), 4)
                    for rem_id in remaining:
                        if per_order[rem_id]["state"] == "PENDING_LOOKUP":
                            per_order[rem_id]["state"] = "UNVERIFIED_ACCESS_DENIED"
                    processed_now = sum(1 for v in per_order.values() if v["state"] == "PROCESSED")
                    non_processed_now = sum(1 for v in per_order.values() if v["state"] == "NON_PROCESSED_STATUS")
                    not_found_now = sum(1 for v in per_order.values() if v["state"] == "NOT_FOUND_YET")
                    unverified_now = sum(
                        1
                        for v in per_order.values()
                        if v["state"] in ("PENDING_LOOKUP", "QUERY_ERROR", "UNVERIFIED_ACCESS_DENIED")
                    )
                    return {
                        "verificationStatus": "UNVERIFIED_DYNAMODB_ACCESS_ERROR",
                        "tableName": table_name,
                        "orderIdsRequested": len(unique_ids),
                        "processedCount": processed_now,
                        "pendingOrOtherStatusCount": non_processed_now,
                        "notFoundCount": not_found_now,
                        "unverifiedCount": unverified_now,
                        "pollsExecuted": polls_executed,
                        "reconciliationDurationSeconds": elapsed,
                        "perOrder": per_order,
                        "errorCode": safe_code,
                    }
                per_order[oid]["state"] = "QUERY_ERROR"
                per_order[oid]["errorCode"] = safe_code
                if clock_fn() >= deadline:
                    break
                continue

            item = resp.get("Item") if isinstance(resp, dict) else None
            if item and isinstance(item, dict):
                db_status = str(item.get("status", ""))
                per_order[oid]["dbStatus"] = db_status
                if db_status == "PROCESSED":
                    per_order[oid]["state"] = "PROCESSED"
                    remaining.discard(oid)
                else:
                    per_order[oid]["state"] = "NON_PROCESSED_STATUS"
            else:
                per_order[oid]["state"] = "NOT_FOUND_YET"

            if clock_fn() >= deadline:
                break

        remaining_after_poll = deadline - clock_fn()
        if remaining and polls_executed < max_polls and remaining_after_poll > 0:
            sleep_fn(min(backoff, remaining_after_poll))
            backoff = min(backoff * 1.5, 2.0)

    elapsed = round(max(0.0001, clock_fn() - start_t), 4)
    processed_count = sum(1 for v in per_order.values() if v["state"] == "PROCESSED")
    non_processed_count = sum(1 for v in per_order.values() if v["state"] == "NON_PROCESSED_STATUS")
    not_found_count = sum(1 for v in per_order.values() if v["state"] == "NOT_FOUND_YET")
    unverified_count = sum(
        1 for v in per_order.values() if v["state"] in ("PENDING_LOOKUP", "QUERY_ERROR", "UNVERIFIED_ACCESS_DENIED")
    )

    if processed_count == len(unique_ids):
        v_status = "ALL_PROCESSED"
    elif processed_count > 0:
        v_status = "PARTIALLY_PROCESSED"
    elif unverified_count == len(unique_ids):
        v_status = "UNVERIFIED"
    else:
        v_status = "NONE_PROCESSED_WITHIN_TIMEOUT"

    return {
        "verificationStatus": v_status,
        "tableName": table_name,
        "orderIdsRequested": len(unique_ids),
        "processedCount": processed_count,
        "pendingOrOtherStatusCount": non_processed_count,
        "notFoundCount": not_found_count,
        "unverifiedCount": unverified_count,
        "pollsExecuted": polls_executed,
        "reconciliationDurationSeconds": elapsed,
        "perOrder": per_order,
        "errorCode": None,
    }


def run_controlled_load_test(
    *,
    endpoint: str,
    request_count: int = 10,
    rate_limit: float = 2.0,
    timeout_seconds: float = 5.0,
    customer_prefix: str = "CUS-LOAD-W3",
    product_id: str = "P001",
    table_name: str = "Orders",
    region: str = "us-east-1",
    reconcile: bool = True,
    reconcile_timeout: float = 20.0,
    reconcile_max_polls: int = 5,
    dry_run: bool = False,
    execute: bool = False,
    confirm_target: Optional[str] = None,
    http_post_fn: Optional[Callable[[str, Dict[str, Any], float], Tuple[int, str]]] = None,
    dynamodb_table: Any = None,
    run_id: Optional[str] = None,
    clock_fn: Callable[[], float] = time.perf_counter,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    """Execute or dry-run a bounded API load test and optional DynamoDB reconciliation."""
    clean_endpoint, endpoint_host = validate_load_test_config(
        endpoint=endpoint,
        request_count=request_count,
        rate_limit=rate_limit,
        timeout_seconds=timeout_seconds,
        customer_prefix=customer_prefix,
        table_name=table_name,
        reconcile_timeout=reconcile_timeout,
        reconcile_max_polls=reconcile_max_polls,
        dry_run=dry_run,
        execute=execute,
        confirm_target=confirm_target,
    )

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    resolved_run_id = run_id or f"load-w3-{now_utc.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"

    if not execute:
        return {
            "schemaVersion": "1.0",
            "sourceType": "DRY_RUN_PLAN",
            "runId": resolved_run_id,
            "timestampUtc": now_utc.isoformat().replace("+00:00", "Z"),
            "executeMode": False,
            "configuration": {
                "endpointHost": endpoint_host,
                "requestCount": request_count,
                "rateLimitPerSec": rate_limit,
                "timeoutSeconds": timeout_seconds,
                "customerPrefix": customer_prefix.strip(),
                "productId": sanitize_text(product_id, 64),
                "reconcileEnabled": reconcile,
                "tableName": table_name.strip(),
                "reconcileTimeoutSeconds": reconcile_timeout,
                "reconcileMaxPolls": reconcile_max_polls,
            },
            "summary": {
                "requestsAttempted": request_count,
                "http202AcceptedCount": 0,
                "http400Count": 0,
                "http429Count": 0,
                "http5xxCount": 0,
                "timeoutCount": 0,
                "otherErrorCount": 0,
                "orderIdsCollectedCount": 0,
                "missingOrderIdOn202Count": 0,
                "malformed202ResponseCount": 0,
                "apiLatencyMs": compute_latency_stats([]),
                "totalSendElapsedSeconds": None,
            },
            "reconciliation": {
                "verificationStatus": "DRY_RUN_NOT_EXECUTED",
                "tableName": table_name.strip(),
                "orderIdsRequested": 0,
                "processedCount": 0,
                "pendingOrOtherStatusCount": 0,
                "notFoundCount": 0,
                "unverifiedCount": 0,
                "pollsExecuted": 0,
                "reconciliationDurationSeconds": None,
            },
            "requests": [],
            "limitations": [
                "Dry-run mode only: no live HTTP requests or DynamoDB GetItem calls were made.",
                "HTTP 202 confirms Producer accepted and sent the message to SQS; DynamoDB status=PROCESSED is required to confirm Consumer completion.",
            ],
        }

    post_fn = http_post_fn or default_http_post
    min_interval = 1.0 / float(rate_limit)

    requests_log: List[Dict[str, Any]] = []
    latencies_ms: List[float] = []
    collected_order_ids: List[str] = []

    http_202 = 0
    http_400 = 0
    http_429 = 0
    http_5xx = 0
    timeout_count = 0
    other_err = 0
    missing_order_id_202 = 0
    malformed_202 = 0

    send_t0 = clock_fn()
    for idx in range(1, request_count + 1):
        req_id = f"{resolved_run_id}-req-{idx:04d}"
        req_ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        payload = {
            "customerId": f"{customer_prefix.strip()}-{idx:03d}",
            "productId": product_id,
            "quantity": 1,
        }

        call_t0 = clock_fn()
        http_status: Optional[int] = None
        returned_order_id = ""
        error_category = ""

        try:
            status_code, raw_body = post_fn(clean_endpoint, payload, timeout_seconds)
            call_ms = (clock_fn() - call_t0) * 1000.0
            latencies_ms.append(call_ms)
            http_status = int(status_code)

            if http_status == 202:
                http_202 += 1
                try:
                    parsed_body = json.loads(raw_body) if isinstance(raw_body, str) else {}
                except ValueError:
                    parsed_body = None

                if not isinstance(parsed_body, dict):
                    malformed_202 += 1
                    error_category = "MALFORMED_202_JSON"
                else:
                    order_obj = parsed_body.get("order")
                    oid = order_obj.get("orderId") if isinstance(order_obj, dict) else parsed_body.get("orderId")
                    if isinstance(oid, str) and oid.strip():
                        returned_order_id = sanitize_text(oid.strip(), 128)
                        collected_order_ids.append(returned_order_id)
                    else:
                        missing_order_id_202 += 1
                        error_category = "MISSING_ORDER_ID_IN_202"
            elif http_status == 400:
                http_400 += 1
                error_category = "HTTP_400_BAD_REQUEST"
            elif http_status == 429:
                http_429 += 1
                error_category = "HTTP_429_RATE_LIMITED"
            elif 500 <= http_status <= 599:
                http_5xx += 1
                error_category = f"HTTP_{http_status}_SERVER_ERROR"
            else:
                other_err += 1
                error_category = f"HTTP_{http_status}_UNEXPECTED"

        except (TimeoutError, socket.timeout) as _:
            call_ms = (clock_fn() - call_t0) * 1000.0
            latencies_ms.append(call_ms)
            timeout_count += 1
            error_category = "REQUEST_TIMEOUT"
        except urllib.error.URLError as url_exc:
            call_ms = (clock_fn() - call_t0) * 1000.0
            latencies_ms.append(call_ms)
            if isinstance(getattr(url_exc, "reason", None), (TimeoutError, socket.timeout)):
                timeout_count += 1
                error_category = "REQUEST_TIMEOUT"
            else:
                other_err += 1
                error_category = "NETWORK_ERROR"
        except Exception as exc:
            call_ms = (clock_fn() - call_t0) * 1000.0
            latencies_ms.append(call_ms)
            other_err += 1
            error_category = sanitize_text(exc.__class__.__name__, 64)

        requests_log.append(
            {
                "runId": resolved_run_id,
                "requestId": req_id,
                "timestampUtc": req_ts,
                "httpStatus": http_status,
                "responseTimeMs": round(call_ms, 3),
                "orderId": returned_order_id,
                "errorCategory": error_category,
                "reconciledState": "NOT_CHECKED",
            }
        )

        # Honor the requested finite positive rate without capping the pacing sleep
        if idx < request_count and min_interval > 0:
            sleep_fn(min_interval)

    send_elapsed = round(max(0.0001, clock_fn() - send_t0), 4)

    if reconcile:
        reconcile_res = reconcile_orders_dynamodb(
            order_ids=collected_order_ids,
            table_name=table_name.strip(),
            region=region,
            timeout_seconds=reconcile_timeout,
            max_polls=reconcile_max_polls,
            dynamodb_table=dynamodb_table,
            clock_fn=clock_fn,
            sleep_fn=sleep_fn,
        )
        per_order_map = reconcile_res.get("perOrder", {})
        for row in requests_log:
            oid = row.get("orderId")
            if oid and oid in per_order_map:
                row["reconciledState"] = per_order_map[oid].get("state", "UNKNOWN")
    else:
        reconcile_res = {
            "verificationStatus": "RECONCILIATION_DISABLED",
            "tableName": table_name.strip(),
            "orderIdsRequested": len(collected_order_ids),
            "processedCount": 0,
            "pendingOrOtherStatusCount": 0,
            "notFoundCount": 0,
            "unverifiedCount": len(collected_order_ids),
            "pollsExecuted": 0,
            "reconciliationDurationSeconds": 0.0,
            "perOrder": {},
            "errorCode": None,
        }

    return {
        "schemaVersion": "1.0",
        "sourceType": "CONTROLLED_API_LOAD_TEST",
        "runId": resolved_run_id,
        "timestampUtc": now_utc.isoformat().replace("+00:00", "Z"),
        "executeMode": True,
        "configuration": {
            "endpointHost": endpoint_host,
            "requestCount": request_count,
            "rateLimitPerSec": rate_limit,
            "timeoutSeconds": timeout_seconds,
            "customerPrefix": customer_prefix.strip(),
            "productId": sanitize_text(product_id, 64),
            "reconcileEnabled": reconcile,
            "tableName": table_name.strip(),
            "reconcileTimeoutSeconds": reconcile_timeout,
            "reconcileMaxPolls": reconcile_max_polls,
        },
        "summary": {
            "requestsAttempted": request_count,
            "http202AcceptedCount": http_202,
            "http400Count": http_400,
            "http429Count": http_429,
            "http5xxCount": http_5xx,
            "timeoutCount": timeout_count,
            "otherErrorCount": other_err,
            "orderIdsCollectedCount": len(collected_order_ids),
            "missingOrderIdOn202Count": missing_order_id_202,
            "malformed202ResponseCount": malformed_202,
            "apiLatencyMs": compute_latency_stats(latencies_ms),
            "totalSendElapsedSeconds": send_elapsed,
        },
        "reconciliation": reconcile_res,
        "requests": requests_log,
        "limitations": [
            "HTTP 202 only proves Producer accepted the request and sent the message to SQS; Consumer completion is verified separately via DynamoDB GetItem status=PROCESSED.",
            "Rate is bounded (<= 10 req/s) to respect the AWS Learner Lab account concurrency limit (<= 10).",
            "Reconciliation uses read-only DynamoDB GetItem by orderId and never scans or mutates the table.",
            "Reconciliation timeout bounds when new GetItem/backoff steps are issued and caps per-call socket connect/read timeouts with single-attempt SDK execution (no hidden retries), rather than forcibly killing an in-flight OS socket call.",
        ],
    }


def write_load_test_outputs(result: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
    """Write load-test-summary.json and load-test-results.csv to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "load-test-summary.json"
    csv_path = output_dir / "load-test-results.csv"

    summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fieldnames = [
        "runId",
        "requestId",
        "timestampUtc",
        "httpStatus",
        "responseTimeMs",
        "orderId",
        "errorCategory",
        "reconciledState",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.get("requests", []):
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    return {"json": summary_path, "csv": csv_path}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled API Load Test & Read-Only DynamoDB Reconciliation Tool (dry-run by default)."
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Target HTTPS POST /orders endpoint URL (required; no hard-coded URL is used).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of requests to send (1..100, default: 10).",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=2.0,
        help="Request rate in requests/second (<= 10.0, default: 2.0).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-request HTTP timeout in seconds (default: 5.0).",
    )
    parser.add_argument(
        "--customer-prefix",
        default="CUS-LOAD-W3",
        help="CustomerId prefix for test orders (default: CUS-LOAD-W3).",
    )
    parser.add_argument(
        "--product-id",
        default="P001",
        help="ProductId for test orders (default: P001).",
    )
    parser.add_argument(
        "--table-name",
        default="Orders",
        help="DynamoDB table name for read-only GetItem reconciliation (default: Orders).",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS Region for DynamoDB reconciliation (default: us-east-1).",
    )
    parser.add_argument(
        "--no-reconcile",
        action="store_true",
        help="Skip DynamoDB GetItem reconciliation.",
    )
    parser.add_argument(
        "--reconcile-timeout",
        type=float,
        default=20.0,
        help="Total timeout in seconds for DynamoDB polling reconciliation (default: 20.0).",
    )
    parser.add_argument(
        "--reconcile-max-polls",
        type=int,
        default=5,
        help="Maximum polling passes over pending orderIds (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/load-test"),
        help="Directory to write load-test-summary.json and load-test-results.csv.",
    )
    parser.add_argument("--run-id", help="Optional unique run identifier.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run in offline dry-run mode without sending live requests (default when --execute is omitted).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Explicitly authorize live HTTP POST and read-only DynamoDB GetItem calls.",
    )
    parser.add_argument(
        "--confirm-target",
        help="Exact endpoint hostname or full URL confirmation required when --execute is set.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        if args.dry_run and args.execute:
            raise LoadTestError("Conflicting flags: --dry-run and --execute cannot be used together.")
        result = run_controlled_load_test(
            endpoint=args.endpoint,
            request_count=args.count,
            rate_limit=args.rate,
            timeout_seconds=args.timeout,
            customer_prefix=args.customer_prefix,
            product_id=args.product_id,
            table_name=args.table_name,
            region=args.region,
            reconcile=not args.no_reconcile,
            reconcile_timeout=args.reconcile_timeout,
            reconcile_max_polls=args.reconcile_max_polls,
            dry_run=bool(args.dry_run),
            execute=bool(args.execute),
            confirm_target=args.confirm_target,
            run_id=args.run_id,
        )
        if args.output_dir:
            write_load_test_outputs(result, args.output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except LoadTestError as exc:
        print(json.dumps({"status": "ERROR", "error": sanitize_text(str(exc))}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
