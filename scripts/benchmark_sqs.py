"""Week 3 SQS Standard vs FIFO Benchmark Tool (W3-02).

Safe, offline-default SQS API benchmark tool supporting Standard and FIFO queues,
single-group and multi-group ordering checks, duplicate detection, bounded
receive polling, and JSON/CSV output generation.

Never targets production queues ('orders-queue', 'orders-dlq') and never calls
AWS unless --execute (without --dry-run) and matching --confirm-target <queue-name>
are provided.
"""

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse
import uuid

PROTECTED_QUEUE_NAMES = frozenset(
    {
        "orders-queue",
        "orders-dlq",
        "orders-queue.fifo",
        "orders-dlq.fifo",
    }
)
QUEUE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,80}(\.fifo)?$")


class BenchmarkError(Exception):
    """Safe benchmark validation or execution error."""


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


def extract_queue_name(queue_url_or_name: str) -> str:
    """Extract queue name from an SQS QueueUrl or plain queue name."""
    if not isinstance(queue_url_or_name, str) or not queue_url_or_name.strip():
        raise BenchmarkError("Queue target must be a non-empty string.")
    raw = queue_url_or_name.strip()
    if "://" in raw:
        parsed = urlparse(raw)
        if parsed.scheme != "https" or not parsed.netloc.endswith(".amazonaws.com"):
            raise BenchmarkError("Queue URL must use https and an amazonaws.com SQS endpoint.")
        if parsed.params or parsed.query or parsed.fragment:
            raise BenchmarkError("Queue URL must not contain query parameters, params, or fragments.")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) != 2 or not re.fullmatch(r"[0-9]{12}", parts[0]):
            raise BenchmarkError("Queue URL must have exact path /<12-digit-account-id>/<queue-name>.")
        q_name = parts[-1]
    else:
        q_name = raw

    if not QUEUE_NAME_PATTERN.match(q_name):
        raise BenchmarkError(f"Invalid SQS queue name: {sanitize_text(q_name)}")
    return q_name


def validate_benchmark_config(
    *,
    queue_type: str,
    queue_target: str,
    message_count: int,
    batch_size: int,
    rate_limit: float,
    timeout_seconds: float,
    max_polls: int,
    group_count: int,
    dry_run: bool = False,
    execute: bool = False,
    confirm_target: Optional[str] = None,
) -> str:
    """Validate benchmark parameters and enforce production queue protection."""
    if dry_run and execute:
        raise BenchmarkError("Conflicting flags: --dry-run and --execute cannot be used together.")

    norm_type = (queue_type or "").strip().lower()
    if norm_type not in ("standard", "fifo"):
        raise BenchmarkError("queue_type must be either 'standard' or 'fifo'.")

    queue_name = extract_queue_name(queue_target)
    if queue_name.lower() in PROTECTED_QUEUE_NAMES:
        raise BenchmarkError(
            f"Refusing to run benchmark on protected production queue '{queue_name}'. "
            "Use a dedicated test queue (e.g. orders-benchmark-standard or orders-benchmark.fifo)."
        )

    is_fifo_name = queue_name.endswith(".fifo")
    if norm_type == "fifo" and not is_fifo_name:
        raise BenchmarkError(f"FIFO queue name '{queue_name}' must end with '.fifo'.")
    if norm_type == "standard" and is_fifo_name:
        raise BenchmarkError(f"Standard queue name '{queue_name}' must not end with '.fifo'.")

    if type(message_count) is not int or message_count < 1 or message_count > 500:
        raise BenchmarkError("message_count must be an integer between 1 and 500.")
    if type(batch_size) is not int or batch_size < 1 or batch_size > 10:
        raise BenchmarkError("batch_size must be an integer between 1 and 10 (SQS limit).")
    if (
        isinstance(rate_limit, bool)
        or not isinstance(rate_limit, (int, float))
        or not math.isfinite(float(rate_limit))
        or float(rate_limit) <= 0.0
        or float(rate_limit) > 200.0
    ):
        raise BenchmarkError("rate_limit must be a finite number > 0 and <= 200 messages/second.")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or float(timeout_seconds) <= 0.0
        or float(timeout_seconds) > 300.0
    ):
        raise BenchmarkError("timeout_seconds must be a finite number > 0 and <= 300 seconds.")
    if type(max_polls) is not int or max_polls < 1 or max_polls > 200:
        raise BenchmarkError("max_polls must be an integer between 1 and 200.")
    if type(group_count) is not int or group_count < 1 or group_count > 50:
        raise BenchmarkError("group_count must be an integer between 1 and 50.")

    if execute:
        if not confirm_target or confirm_target.strip() != queue_name:
            raise BenchmarkError(
                f"Live execution requires --confirm-target {queue_name} matching the target queue name."
            )

    return queue_name


def compute_latency_stats(values_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    """Compute count, min, max, mean, median, and p95 in milliseconds."""
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
    if n % 2 == 1:
        median = clean[mid]
    else:
        median = (clean[mid - 1] + clean[mid]) / 2.0

    p95_idx = max(0, min(n - 1, math.ceil(0.95 * n) - 1))
    p95 = clean[p95_idx]
    return {
        "count": n,
        "minMs": round(clean[0], 3),
        "maxMs": round(clean[-1], 3),
        "meanMs": round(sum(clean) / n, 3),
        "medianMs": round(median, 3),
        "p95Ms": round(p95, 3),
    }


def analyze_ordering(received_sequences_by_group: Dict[str, List[int]]) -> Dict[str, Any]:
    """Evaluate per-group and global ordering from received sequence numbers."""
    per_group_results: Dict[str, Dict[str, Any]] = {}
    out_of_order_groups = 0
    total_inversions = 0

    for group_id, seq_list in sorted(received_sequences_by_group.items()):
        inversions = 0
        for idx in range(1, len(seq_list)):
            if seq_list[idx] < seq_list[idx - 1]:
                inversions += 1
        in_order = inversions == 0
        if not in_order:
            out_of_order_groups += 1
        total_inversions += inversions
        per_group_results[group_id] = {
            "receivedCount": len(seq_list),
            "inOrder": in_order,
            "outOfOrderTransitions": inversions,
            "sequenceSample": seq_list[:20],
        }

    return {
        "evaluatedGroups": len(per_group_results),
        "allGroupsInOrder": out_of_order_groups == 0 if per_group_results else None,
        "outOfOrderGroups": out_of_order_groups,
        "totalOutOfOrderTransitions": total_inversions,
        "perGroup": per_group_results,
        "note": (
            "FIFO guarantees ordering within each MessageGroupId, not global ordering across distinct groups."
        ),
    }


def build_benchmark_message(
    *,
    run_id: str,
    seq: int,
    queue_type: str,
    group_count: int,
    dedup_mode: str = "explicit",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build benchmark message body and SQS send parameters."""
    group_id = f"bench-group-{(seq - 1) % group_count + 1:02d}"
    order_id = f"BENCH-{run_id}-{seq:04d}"
    payload = {
        "benchmarkRunId": run_id,
        "sequenceNumber": seq,
        "messageGroupId": group_id,
        "orderId": order_id,
        "customerId": f"CUS-BENCH-{(seq - 1) % group_count + 1:02d}",
        "productId": "PROD-BENCH-01",
        "quantity": 1,
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    send_kwargs: Dict[str, Any] = {
        "MessageBody": json.dumps(payload),
    }
    if queue_type == "fifo":
        send_kwargs["MessageGroupId"] = group_id
        if dedup_mode == "explicit":
            send_kwargs["MessageDeduplicationId"] = f"{run_id}-{seq:04d}"
    return payload, send_kwargs


def build_bounded_boto_config(timeout_seconds: float) -> Any:
    """Build a botocore Config with single-attempt execution (no hidden retries) and per-call socket timeouts bounded by timeout_seconds."""
    from botocore.config import Config  # type: ignore

    budget = max(0.05, float(timeout_seconds))
    per_call_timeout = min(10.0, budget)
    return Config(
        connect_timeout=per_call_timeout,
        read_timeout=per_call_timeout,
        retries={"total_max_attempts": 1, "max_attempts": 0, "mode": "standard"},
    )


def resolve_canonical_queue_url(queue_url_or_name: str, queue_name: str, sqs_client: Any) -> str:
    """Return a validated full HTTPS SQS QueueUrl, resolving bare queue names via get_queue_url."""
    raw = queue_url_or_name.strip()
    if "://" in raw:
        return raw
    get_url_fn = getattr(sqs_client, "get_queue_url", None)
    if not callable(get_url_fn):
        raise BenchmarkError("SQS client does not support get_queue_url for bare queue name resolution.")
    try:
        resp = get_url_fn(QueueName=queue_name)
    except Exception as exc:
        err_code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
        safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
        raise BenchmarkError(f"Failed to resolve SQS QueueUrl for '{queue_name}': {safe_code}") from exc
    resolved = resp.get("QueueUrl", "") if isinstance(resp, dict) else ""
    if not isinstance(resolved, str) or "://" not in resolved.strip():
        raise BenchmarkError(f"get_queue_url did not return a valid full QueueUrl for '{queue_name}'.")
    clean_url = resolved.strip()
    resolved_name = extract_queue_name(clean_url)
    if resolved_name != queue_name:
        raise BenchmarkError(
            f"Resolved QueueUrl queue name '{resolved_name}' does not match requested queue '{queue_name}'."
        )
    return clean_url


def run_sqs_benchmark(
    *,
    queue_type: str,
    queue_url: str,
    message_count: int = 20,
    batch_size: int = 1,
    rate_limit: float = 20.0,
    timeout_seconds: float = 15.0,
    max_polls: int = 25,
    group_count: int = 1,
    dedup_mode: str = "explicit",
    dry_run: bool = False,
    execute: bool = False,
    confirm_target: Optional[str] = None,
    sqs_client: Any = None,
    run_id: Optional[str] = None,
    clock_fn: Callable[[], float] = time.perf_counter,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    """Run SQS Standard or FIFO benchmark (dry-run by default unless execute=True)."""
    norm_type = (queue_type or "").strip().lower()
    queue_name = validate_benchmark_config(
        queue_type=norm_type,
        queue_target=queue_url,
        message_count=message_count,
        batch_size=batch_size,
        rate_limit=rate_limit,
        timeout_seconds=timeout_seconds,
        max_polls=max_polls,
        group_count=group_count,
        dry_run=dry_run,
        execute=execute,
        confirm_target=confirm_target,
    )

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    resolved_run_id = run_id or f"sqs-bench-{norm_type}-{now_utc.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"

    if not execute:
        sample_payload, sample_kwargs = build_benchmark_message(
            run_id=resolved_run_id,
            seq=1,
            queue_type=norm_type,
            group_count=group_count,
            dedup_mode=dedup_mode,
        )
        return {
            "schemaVersion": "1.0",
            "benchmarkScope": "SQS_API_ISOLATED",
            "sourceType": "DRY_RUN_PLAN",
            "runId": resolved_run_id,
            "timestampUtc": now_utc.isoformat().replace("+00:00", "Z"),
            "executeMode": False,
            "configuration": {
                "queueType": norm_type,
                "queueName": queue_name,
                "messageCount": message_count,
                "batchSize": batch_size,
                "rateLimitPerSec": rate_limit,
                "timeoutSeconds": timeout_seconds,
                "maxPolls": max_polls,
                "groupCount": group_count if norm_type == "fifo" else 1,
                "deduplicationMode": dedup_mode if norm_type == "fifo" else "not_applicable",
            },
            "metrics": {
                "attemptedMessages": message_count,
                "acceptedSends": 0,
                "failedSends": 0,
                "uniqueReceivedMessages": 0,
                "duplicateObservations": 0,
                "receiveCompletenessRatio": None,
                "elapsedSendSeconds": None,
                "elapsedReceiveSeconds": None,
                "totalElapsedSeconds": None,
                "sendThroughputMsgPerSec": None,
                "receiveThroughputMsgPerSec": None,
                "sendLatencyMs": compute_latency_stats([]),
                "receivePollLatencyMs": compute_latency_stats([]),
            },
            "ordering": analyze_ordering({}),
            "sampleMessagePreview": {
                "orderId": sample_payload["orderId"],
                "hasMessageGroupId": "MessageGroupId" in sample_kwargs,
                "hasMessageDeduplicationId": "MessageDeduplicationId" in sample_kwargs,
            },
            "records": [],
            "limitations": [
                "Dry-run mode only: no live AWS SQS calls were executed.",
                "SQS API benchmark measures SendMessage/ReceiveMessage latency, not Consumer Lambda + DynamoDB E2E completion.",
            ],
        }

    if sqs_client is None:
        try:
            import boto3  # type: ignore
        except ModuleNotFoundError as exc:
            raise BenchmarkError("boto3 is required for live SQS benchmark execution.") from exc
        boto_cfg = build_bounded_boto_config(timeout_seconds)
        sqs_client = boto3.client("sqs", region_name="us-east-1", config=boto_cfg)

    resolved_queue_url = resolve_canonical_queue_url(queue_url, queue_name, sqs_client)

    send_latencies_ms: List[float] = []
    receive_poll_latencies_ms: List[float] = []
    accepted_sends = 0
    failed_sends = 0
    records_out: List[Dict[str, Any]] = []

    # Track exact accepted message identities (orderId, sqsMessageId, sequenceNumber, groupId)
    # so only messages actually accepted by SQS in THIS invocation are counted or deleted.
    accepted_by_order_id: Dict[str, Dict[str, Any]] = {}
    accepted_sqs_message_ids: Set[str] = set()

    min_interval = 1.0 / float(rate_limit)
    send_start_t = clock_fn()

    seq = 1
    while seq <= message_count:
        count_in_call = min(batch_size, message_count - seq + 1)
        call_start = clock_fn()

        if batch_size == 1:
            payload, send_kwargs = build_benchmark_message(
                run_id=resolved_run_id,
                seq=seq,
                queue_type=norm_type,
                group_count=group_count,
                dedup_mode=dedup_mode,
            )
            try:
                resp = sqs_client.send_message(QueueUrl=resolved_queue_url, **send_kwargs)
                call_ms = (clock_fn() - call_start) * 1000.0
                send_latencies_ms.append(call_ms)
                msg_id = sanitize_text(resp.get("MessageId", ""), 128)
                accepted_sends += 1
                if msg_id:
                    accepted_sqs_message_ids.add(msg_id)
                accepted_by_order_id[payload["orderId"]] = {
                    "sqsMessageId": msg_id,
                    "sequenceNumber": seq,
                    "messageGroupId": payload["messageGroupId"],
                }
                records_out.append(
                    {
                        "runId": resolved_run_id,
                        "phase": "SEND",
                        "sequenceNumber": seq,
                        "orderId": payload["orderId"],
                        "messageGroupId": payload["messageGroupId"] if norm_type == "fifo" else "",
                        "sqsMessageId": msg_id,
                        "status": "ACCEPTED",
                        "latencyMs": round(call_ms, 3),
                        "errorCode": "",
                    }
                )
            except Exception as exc:
                call_ms = (clock_fn() - call_start) * 1000.0
                send_latencies_ms.append(call_ms)
                failed_sends += 1
                err_code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
                safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
                records_out.append(
                    {
                        "runId": resolved_run_id,
                        "phase": "SEND",
                        "sequenceNumber": seq,
                        "orderId": payload["orderId"],
                        "messageGroupId": payload["messageGroupId"] if norm_type == "fifo" else "",
                        "sqsMessageId": "",
                        "status": "FAILED",
                        "latencyMs": round(call_ms, 3),
                        "errorCode": safe_code,
                    }
                )
            seq += 1
        else:
            entries = []
            batch_meta = {}
            for offset in range(count_in_call):
                cur_seq = seq + offset
                payload, send_kwargs = build_benchmark_message(
                    run_id=resolved_run_id,
                    seq=cur_seq,
                    queue_type=norm_type,
                    group_count=group_count,
                    dedup_mode=dedup_mode,
                )
                entry_id = f"msg-{cur_seq:04d}"
                entry: Dict[str, Any] = {
                    "Id": entry_id,
                    "MessageBody": send_kwargs["MessageBody"],
                }
                if "MessageGroupId" in send_kwargs:
                    entry["MessageGroupId"] = send_kwargs["MessageGroupId"]
                if "MessageDeduplicationId" in send_kwargs:
                    entry["MessageDeduplicationId"] = send_kwargs["MessageDeduplicationId"]
                entries.append(entry)
                batch_meta[entry_id] = (cur_seq, payload)

            try:
                resp = sqs_client.send_message_batch(QueueUrl=resolved_queue_url, Entries=entries)
                call_ms = (clock_fn() - call_start) * 1000.0
                send_latencies_ms.append(call_ms)
                successful = {item["Id"]: item for item in resp.get("Successful", [])}
                failed = {item["Id"]: item for item in resp.get("Failed", [])}
                for entry_id, (cur_seq, payload) in batch_meta.items():
                    if entry_id in successful:
                        msg_id = sanitize_text(successful[entry_id].get("MessageId", ""), 128)
                        accepted_sends += 1
                        if msg_id:
                            accepted_sqs_message_ids.add(msg_id)
                        accepted_by_order_id[payload["orderId"]] = {
                            "sqsMessageId": msg_id,
                            "sequenceNumber": cur_seq,
                            "messageGroupId": payload["messageGroupId"],
                        }
                        records_out.append(
                            {
                                "runId": resolved_run_id,
                                "phase": "SEND",
                                "sequenceNumber": cur_seq,
                                "orderId": payload["orderId"],
                                "messageGroupId": payload["messageGroupId"] if norm_type == "fifo" else "",
                                "sqsMessageId": msg_id,
                                "status": "ACCEPTED",
                                "latencyMs": round(call_ms, 3),
                                "errorCode": "",
                            }
                        )
                    else:
                        failed_sends += 1
                        fail_info = failed.get(entry_id, {})
                        records_out.append(
                            {
                                "runId": resolved_run_id,
                                "phase": "SEND",
                                "sequenceNumber": cur_seq,
                                "orderId": payload["orderId"],
                                "messageGroupId": payload["messageGroupId"] if norm_type == "fifo" else "",
                                "sqsMessageId": "",
                                "status": "FAILED",
                                "latencyMs": round(call_ms, 3),
                                "errorCode": sanitize_text(fail_info.get("Code", "BATCH_ENTRY_FAILED"), 64),
                            }
                        )
            except Exception as exc:
                call_ms = (clock_fn() - call_start) * 1000.0
                send_latencies_ms.append(call_ms)
                err_code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
                safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
                for _, (cur_seq, payload) in batch_meta.items():
                    failed_sends += 1
                    records_out.append(
                        {
                            "runId": resolved_run_id,
                            "phase": "SEND",
                            "sequenceNumber": cur_seq,
                            "orderId": payload["orderId"],
                            "messageGroupId": payload["messageGroupId"] if norm_type == "fifo" else "",
                            "sqsMessageId": "",
                            "status": "FAILED",
                            "latencyMs": round(call_ms, 3),
                            "errorCode": safe_code,
                        }
                    )
            seq += count_in_call

        # Honor the requested finite positive rate without capping the pacing sleep
        if seq <= message_count and min_interval > 0:
            sleep_fn(min_interval * count_in_call)

    send_elapsed = max(0.0001, clock_fn() - send_start_t)

    # Bounded receive loop: check observation deadline before every receive_message and every per-message delete_message
    receive_start_t = clock_fn()
    receive_deadline = receive_start_t + float(timeout_seconds)
    seen_order_ids: Set[str] = set()
    seen_sqs_message_ids: Set[str] = set()
    duplicate_observations = 0
    received_by_group: Dict[str, List[int]] = {}
    polls_executed = 0

    while (
        polls_executed < max_polls
        and len(seen_order_ids) < accepted_sends
        and clock_fn() < receive_deadline
    ):
        remaining_budget = receive_deadline - clock_fn()
        if remaining_budget <= 0:
            break
        polls_executed += 1
        poll_t0 = clock_fn()
        wait_seconds = 1 if remaining_budget >= 1.5 else 0
        try:
            recv_resp = sqs_client.receive_message(
                QueueUrl=resolved_queue_url,
                MaxNumberOfMessages=min(10, max(1, batch_size)),
                WaitTimeSeconds=wait_seconds,
                AttributeNames=["All"],
            )
            poll_ms = (clock_fn() - poll_t0) * 1000.0
            receive_poll_latencies_ms.append(poll_ms)
        except Exception as exc:
            poll_ms = (clock_fn() - poll_t0) * 1000.0
            receive_poll_latencies_ms.append(poll_ms)
            err_code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
            safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
            records_out.append(
                {
                    "runId": resolved_run_id,
                    "phase": "RECEIVE_POLL",
                    "sequenceNumber": polls_executed,
                    "orderId": "",
                    "messageGroupId": "",
                    "sqsMessageId": "",
                    "status": "POLL_ERROR",
                    "latencyMs": round(poll_ms, 3),
                    "errorCode": safe_code,
                }
            )
            break

        messages = recv_resp.get("Messages", [])
        if not messages:
            continue

        for msg in messages:
            if clock_fn() >= receive_deadline:
                break
            receipt_handle = msg.get("ReceiptHandle")
            msg_id = sanitize_text(msg.get("MessageId", ""), 128)
            raw_body = msg.get("Body", "{}")
            try:
                parsed_body = json.loads(raw_body) if isinstance(raw_body, str) else {}
            except ValueError:
                parsed_body = {}

            if not isinstance(parsed_body, dict):
                continue

            ord_id = str(parsed_body.get("orderId", ""))
            # Verify ownership against both the accepted orderId and the SQS MessageId
            # returned when this invocation sent the message (never rely solely on a reusable runId).
            if (
                parsed_body.get("benchmarkRunId") != resolved_run_id
                or ord_id not in accepted_by_order_id
                or not msg_id
                or msg_id not in accepted_sqs_message_ids
                or accepted_by_order_id[ord_id].get("sqsMessageId") != msg_id
            ):
                continue

            seq_num = parsed_body.get("sequenceNumber")
            grp_id = str(
                parsed_body.get("messageGroupId")
                or msg.get("Attributes", {}).get("MessageGroupId")
                or "default"
            )

            if ord_id in seen_order_ids or msg_id in seen_sqs_message_ids:
                duplicate_observations += 1
                recv_status = "DUPLICATE_DELIVERY"
            else:
                seen_order_ids.add(ord_id)
                seen_sqs_message_ids.add(msg_id)
                recv_status = "UNIQUE_RECEIVED"
                if isinstance(seq_num, int):
                    received_by_group.setdefault(grp_id, []).append(seq_num)

            if receipt_handle and clock_fn() < receive_deadline:
                try:
                    sqs_client.delete_message(QueueUrl=resolved_queue_url, ReceiptHandle=receipt_handle)
                except Exception:
                    pass

            records_out.append(
                {
                    "runId": resolved_run_id,
                    "phase": "RECEIVE",
                    "sequenceNumber": seq_num if isinstance(seq_num, int) else 0,
                    "orderId": ord_id,
                    "messageGroupId": grp_id if norm_type == "fifo" else "",
                    "sqsMessageId": msg_id,
                    "status": recv_status,
                    "latencyMs": round(poll_ms, 3),
                    "errorCode": "",
                }
            )

    receive_elapsed = max(0.0001, clock_fn() - receive_start_t)
    total_elapsed = send_elapsed + receive_elapsed
    unique_received = len(seen_order_ids)
    completeness = round(unique_received / accepted_sends, 4) if accepted_sends > 0 else 0.0

    return {
        "schemaVersion": "1.0",
        "benchmarkScope": "SQS_API_ISOLATED",
        "sourceType": "SQS_BENCHMARK_RUN",
        "runId": resolved_run_id,
        "timestampUtc": now_utc.isoformat().replace("+00:00", "Z"),
        "executeMode": True,
        "configuration": {
            "queueType": norm_type,
            "queueName": queue_name,
            "messageCount": message_count,
            "batchSize": batch_size,
            "rateLimitPerSec": rate_limit,
            "timeoutSeconds": timeout_seconds,
            "maxPolls": max_polls,
            "groupCount": group_count if norm_type == "fifo" else 1,
            "deduplicationMode": dedup_mode if norm_type == "fifo" else "not_applicable",
        },
        "metrics": {
            "attemptedMessages": message_count,
            "acceptedSends": accepted_sends,
            "failedSends": failed_sends,
            "uniqueReceivedMessages": unique_received,
            "duplicateObservations": duplicate_observations,
            "receiveCompletenessRatio": completeness,
            "pollsExecuted": polls_executed,
            "elapsedSendSeconds": round(send_elapsed, 4),
            "elapsedReceiveSeconds": round(receive_elapsed, 4),
            "totalElapsedSeconds": round(total_elapsed, 4),
            "sendThroughputMsgPerSec": round(accepted_sends / send_elapsed, 3) if accepted_sends > 0 else 0.0,
            "receiveThroughputMsgPerSec": round(unique_received / receive_elapsed, 3) if unique_received > 0 else 0.0,
            "sendLatencyMs": compute_latency_stats(send_latencies_ms),
            "receivePollLatencyMs": compute_latency_stats(receive_poll_latencies_ms),
        },
        "ordering": analyze_ordering(received_by_group),
        "records": records_out,
        "limitations": [
            "SQS API benchmark measures direct SQS SendMessage/ReceiveMessage behavior, not Consumer Lambda + DynamoDB processing time.",
            "Redelivered messages with the same orderId are counted under duplicateObservations and never inflated as uniqueReceivedMessages.",
            "FIFO ordering applies within each MessageGroupId; multi-group runs interleave across groups by design.",
            "Absence of duplicates in a small Standard queue sample does not prove Standard queues never duplicate messages.",
            "Observation timeout bounds when new poll/delete calls are issued and caps per-call socket connect/read timeouts with single-attempt SDK execution (no hidden retries), rather than forcibly killing an in-flight OS socket call.",
        ],
    }


def write_benchmark_outputs(result: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
    """Write benchmark-summary.json and benchmark-results.csv to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "benchmark-summary.json"
    csv_path = output_dir / "benchmark-results.csv"

    summary_payload = dict(result)
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fieldnames = [
        "runId",
        "phase",
        "sequenceNumber",
        "orderId",
        "messageGroupId",
        "sqsMessageId",
        "status",
        "latencyMs",
        "errorCode",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.get("records", []):
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    return {"json": summary_path, "csv": csv_path}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe SQS Standard vs FIFO Benchmark Tool (offline dry-run by default)."
    )
    parser.add_argument(
        "--queue-type",
        required=True,
        choices=["standard", "fifo"],
        help="Target SQS queue type: 'standard' or 'fifo'.",
    )
    parser.add_argument(
        "--queue-url",
        required=True,
        help="Dedicated benchmark SQS Queue URL or queue name (never orders-queue or orders-dlq).",
    )
    parser.add_argument(
        "--message-count",
        type=int,
        default=20,
        help="Number of messages to benchmark (1..500, default: 20).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="SQS send/receive batch size (1..10, default: 1).",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=20.0,
        help="Target send rate in messages/second (default: 20.0).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Bounded receive loop timeout in seconds (default: 15.0).",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=25,
        help="Maximum ReceiveMessage poll iterations (default: 25).",
    )
    parser.add_argument(
        "--group-count",
        type=int,
        default=1,
        help="Number of MessageGroupIds for FIFO benchmark (1=single-group, >1=multi-group).",
    )
    parser.add_argument(
        "--dedup-mode",
        choices=["explicit", "content-based"],
        default="explicit",
        help="FIFO deduplication mode: explicit MessageDeduplicationId or content-based.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/benchmark"),
        help="Output directory for benchmark-summary.json and benchmark-results.csv.",
    )
    parser.add_argument("--run-id", help="Optional unique run identifier.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Generate dry-run plan without calling AWS (default when --execute is omitted).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Explicitly enable live SQS API benchmark calls (requires --confirm-target).",
    )
    parser.add_argument(
        "--confirm-target",
        help="Exact benchmark queue name confirmation required when --execute is set.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        if args.dry_run and args.execute:
            raise BenchmarkError("Conflicting flags: --dry-run and --execute cannot be used together.")
        result = run_sqs_benchmark(
            queue_type=args.queue_type,
            queue_url=args.queue_url,
            message_count=args.message_count,
            batch_size=args.batch_size,
            rate_limit=args.rate,
            timeout_seconds=args.timeout,
            max_polls=args.max_polls,
            group_count=args.group_count,
            dedup_mode=args.dedup_mode,
            dry_run=bool(args.dry_run),
            execute=bool(args.execute),
            confirm_target=args.confirm_target,
            run_id=args.run_id,
        )
        if args.output_dir:
            write_benchmark_outputs(result, args.output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except BenchmarkError as exc:
        print(json.dumps({"status": "ERROR", "error": sanitize_text(str(exc))}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
