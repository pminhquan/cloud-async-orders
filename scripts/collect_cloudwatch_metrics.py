"""Week 3 CloudWatch Monitoring & Metrics Collector (W3-01 & W3-04).

Safe, offline-default utility for collecting SQS queue backlog, DLQ visible
messages, Lambda Errors/Duration/Throttles, and CloudWatch Alarm states.
Never fabricates zero values or timestamps for missing datapoints and never
logs secrets or account credentials.
"""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Sequence
import uuid

ALLOWED_REGIONS = ("us-east-1", "us-west-2")
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


class MetricsCollectionError(Exception):
    """Safe error raised when configuration or collection fails."""


def sanitize_text(value: Any, max_length: int = 160) -> str:
    """Sanitize strings for safe output and redact accidental account/key patterns."""
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


def parse_utc_timestamp(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp string and normalize to UTC."""
    if not isinstance(raw, str) or not raw.strip():
        raise MetricsCollectionError("Timestamp must be a non-empty ISO-8601 string.")
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise MetricsCollectionError(f"Invalid ISO-8601 timestamp: {sanitize_text(raw)}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def format_utc(dt: datetime) -> str:
    """Format datetime as canonical ISO-8601 UTC string with Z suffix."""
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_resource_name(name: str, label: str) -> str:
    """Validate AWS resource name to prevent injection or malformed dimensions."""
    if not isinstance(name, str) or not name.strip():
        raise MetricsCollectionError(f"{label} must be a non-empty string.")
    candidate = name.strip()
    if len(candidate) > 128 or not NAME_PATTERN.match(candidate):
        raise MetricsCollectionError(f"Invalid {label}: {sanitize_text(name)}")
    return candidate


CW_RECEIPT_MARGIN_SECONDS = 300


def estimate_get_metric_statistics_datapoints(
    start_time: datetime,
    end_time: datetime,
    period_seconds: int,
    now_utc: Optional[datetime] = None,
) -> int:
    """Estimate conservative upper-bound CloudWatch GetMetricStatistics datapoints.

    AWS evaluates StartTime age when receiving each request and floors StartTime to
    60s (<15d), 300s (15..63d), or 3600s (>63d). Taking the worst-case across
    [ref_utc, ref_utc + CW_RECEIPT_MARGIN_SECONDS] prevents a request validated just
    before the 15-day or 63-day boundary from crossing into a coarser floor grid on
    receipt and exceeding 1440 datapoints.
    """
    s_utc = start_time.astimezone(timezone.utc) if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)
    e_utc = end_time.astimezone(timezone.utc) if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
    ref_utc = (
        (now_utc.astimezone(timezone.utc) if now_utc.tzinfo else now_utc.replace(tzinfo=timezone.utc))
        if now_utc is not None
        else datetime.now(timezone.utc)
    )
    age_now = max(0.0, (ref_utc - s_utc).total_seconds())
    age_receipt = age_now + CW_RECEIPT_MARGIN_SECONDS

    grids = set()
    for age in (age_now, age_receipt):
        if age > 63 * 86400:
            grids.add(3600)
        elif age >= 15 * 86400:
            grids.add(300)
        else:
            grids.add(60)

    return max(
        math.ceil((e_utc.timestamp() - (math.floor(s_utc.timestamp() / g) * g)) / period_seconds)
        for g in grids
    )


def validate_config(
    region: str,
    queues: Sequence[str],
    functions: Sequence[str],
    period_seconds: int,
    start_time: datetime,
    end_time: datetime,
    dry_run: bool = False,
    execute: bool = False,
    now_utc: Optional[datetime] = None,
) -> None:
    """Validate collector parameters before dry-run or live execution."""
    if dry_run and execute:
        raise MetricsCollectionError("Conflicting flags: --dry-run and --execute cannot be used together.")
    if region not in ALLOWED_REGIONS:
        raise MetricsCollectionError(
            f"Unsupported region '{sanitize_text(region)}'. Allowed: {', '.join(ALLOWED_REGIONS)}"
        )
    if not queues and not functions:
        raise MetricsCollectionError("At least one queue or Lambda function must be specified.")
    for q in queues:
        validate_resource_name(q, "queue name")
    for fn in functions:
        validate_resource_name(fn, "Lambda function name")
    if type(period_seconds) is not int or period_seconds < 60 or period_seconds % 60 != 0:
        raise MetricsCollectionError("period_seconds must be an integer multiple of 60 (>= 60).")
    if end_time <= start_time:
        raise MetricsCollectionError("end_time must be strictly greater than start_time.")
    window_seconds = (end_time - start_time).total_seconds()
    if window_seconds > 86400 * 7:
        raise MetricsCollectionError("Observation window cannot exceed 7 days.")
    if estimate_get_metric_statistics_datapoints(start_time, end_time, period_seconds, now_utc=now_utc) > 1440:
        raise MetricsCollectionError(
            "Requested window and period would exceed CloudWatch GetMetricStatistics limit of 1440 datapoints."
        )


def build_metric_specs(
    queues: Sequence[str],
    functions: Sequence[str],
) -> List[Dict[str, Any]]:
    """Build standard CloudWatch metric queries for SQS queues and Lambda functions."""
    specs: List[Dict[str, Any]] = []
    for q_name in queues:
        for metric_name, stat, unit in (
            ("ApproximateNumberOfMessagesVisible", "Maximum", "Count"),
            ("ApproximateNumberOfMessagesNotVisible", "Maximum", "Count"),
            ("ApproximateAgeOfOldestMessage", "Maximum", "Seconds"),
            ("NumberOfMessagesSent", "Sum", "Count"),
            ("NumberOfMessagesReceived", "Sum", "Count"),
            ("NumberOfMessagesDeleted", "Sum", "Count"),
        ):
            specs.append(
                {
                    "resourceType": "SQS",
                    "resourceName": q_name,
                    "namespace": "AWS/SQS",
                    "dimensionName": "QueueName",
                    "dimensionValue": q_name,
                    "metricName": metric_name,
                    "statistic": stat,
                    "unit": unit,
                }
            )
    for fn_name in functions:
        for metric_name, stat, unit in (
            ("Invocations", "Sum", "Count"),
            ("Errors", "Sum", "Count"),
            ("Throttles", "Sum", "Count"),
            ("Duration", "Average", "Milliseconds"),
            ("Duration", "Maximum", "Milliseconds"),
            ("ConcurrentExecutions", "Maximum", "Count"),
        ):
            specs.append(
                {
                    "resourceType": "Lambda",
                    "resourceName": fn_name,
                    "namespace": "AWS/Lambda",
                    "dimensionName": "FunctionName",
                    "dimensionValue": fn_name,
                    "metricName": metric_name,
                    "statistic": stat,
                    "unit": unit,
                }
            )
    return specs


def summarize_datapoints(
    datapoints: Sequence[Dict[str, Any]],
    statistic: str,
) -> Dict[str, Any]:
    """Summarize CloudWatch datapoints without fabricating 0 or timestamps for missing/invalid data."""
    if not datapoints:
        return {
            "status": "NO_DATA",
            "datapointCount": 0,
            "latestValue": None,
            "latestTimestamp": None,
            "minValue": None,
            "maxValue": None,
            "meanValue": None,
            "sumValue": None,
            "note": "No datapoints returned by CloudWatch; value is left null (not assumed 0).",
        }

    normalized: List[Dict[str, Any]] = []
    invalid_timestamp_or_value = 0
    for dp in datapoints:
        if not isinstance(dp, dict) or statistic not in dp or dp[statistic] is None:
            continue
        raw_val = dp[statistic]
        if isinstance(raw_val, bool) or not isinstance(raw_val, (int, float)):
            invalid_timestamp_or_value += 1
            continue
        val = float(raw_val)
        if not math.isfinite(val):
            invalid_timestamp_or_value += 1
            continue

        raw_ts = dp.get("Timestamp")
        if isinstance(raw_ts, datetime):
            dt = raw_ts.astimezone(timezone.utc) if raw_ts.tzinfo else raw_ts.replace(tzinfo=timezone.utc)
        elif isinstance(raw_ts, str) and raw_ts.strip():
            try:
                dt = parse_utc_timestamp(raw_ts)
            except MetricsCollectionError:
                invalid_timestamp_or_value += 1
                continue
        else:
            # Never invent a timestamp when Timestamp is missing or invalid
            invalid_timestamp_or_value += 1
            continue

        normalized.append({"timestamp": dt, "value": val, "unit": dp.get("Unit")})

    if not normalized:
        status_code = "INVALID_DATAPOINTS" if invalid_timestamp_or_value > 0 else "NO_DATA"
        note_msg = (
            "Datapoints had missing/invalid Timestamp or non-finite values; left null without inventing timestamps."
            if invalid_timestamp_or_value > 0
            else "Datapoints lacked requested statistic; value left null."
        )
        return {
            "status": status_code,
            "datapointCount": 0,
            "latestValue": None,
            "latestTimestamp": None,
            "minValue": None,
            "maxValue": None,
            "meanValue": None,
            "sumValue": None,
            "note": note_msg,
        }

    normalized.sort(key=lambda item: item["timestamp"])
    values = [item["value"] for item in normalized]
    latest = normalized[-1]
    return {
        "status": "OK",
        "datapointCount": len(values),
        "latestValue": round(latest["value"], 4),
        "latestTimestamp": format_utc(latest["timestamp"]),
        "minValue": round(min(values), 4),
        "maxValue": round(max(values), 4),
        "meanValue": round(sum(values) / len(values), 4),
        "sumValue": round(sum(values), 4) if statistic == "Sum" else None,
        "note": "Measured from CloudWatch datapoints.",
    }


def collect_cloudwatch_metrics(
    *,
    region: str = "us-east-1",
    queues: Sequence[str] = ("orders-queue", "orders-dlq"),
    functions: Sequence[str] = ("order-producer", "order-consumer"),
    alarm_names: Sequence[str] = (),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    period_seconds: int = 60,
    dry_run: bool = False,
    execute: bool = False,
    cloudwatch_client: Any = None,
    run_id: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Collect or dry-run CloudWatch metrics and optional alarm states."""
    raw_now = (
        (now_utc.astimezone(timezone.utc) if now_utc.tzinfo else now_utc.replace(tzinfo=timezone.utc))
        if now_utc is not None
        else datetime.now(timezone.utc)
    )
    now_ts = raw_now.replace(microsecond=0)
    resolved_end = end_time or now_ts
    resolved_start = start_time or (resolved_end - timedelta(minutes=30))
    validate_config(
        region,
        queues,
        functions,
        period_seconds,
        resolved_start,
        resolved_end,
        dry_run=dry_run,
        execute=execute,
        now_utc=raw_now,
    )

    for alarm in alarm_names:
        validate_resource_name(alarm, "alarm name")

    resolved_run_id = run_id or f"metrics-{now_ts.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    specs = build_metric_specs(queues, functions)

    if not execute and cloudwatch_client is None:
        records = []
        for spec in specs:
            records.append(
                {
                    **spec,
                    "periodSeconds": period_seconds,
                    "startTime": format_utc(resolved_start),
                    "endTime": format_utc(resolved_end),
                    "status": "DRY_RUN_NOT_EXECUTED",
                    "datapointCount": 0,
                    "latestValue": None,
                    "latestTimestamp": None,
                    "minValue": None,
                    "maxValue": None,
                    "meanValue": None,
                    "sumValue": None,
                    "errorCode": None,
                    "note": "Dry-run mode: no live AWS CloudWatch call was made.",
                }
            )
        alarms_summary = [
            {
                "alarmName": name,
                "stateValue": "DRY_RUN_NOT_QUERIED",
                "metricName": None,
                "namespace": None,
                "updatedTimestamp": None,
                "errorCode": None,
            }
            for name in alarm_names
        ]
        return {
            "schemaVersion": "1.0",
            "sourceType": "DRY_RUN_PLAN",
            "runId": resolved_run_id,
            "collectedAt": format_utc(now_ts),
            "region": region,
            "windowStart": format_utc(resolved_start),
            "windowEnd": format_utc(resolved_end),
            "periodSeconds": period_seconds,
            "executeMode": False,
            "metrics": records,
            "alarms": alarms_summary,
            "limitations": [
                "Dry-run mode only: no live AWS CloudWatch API requests were executed.",
                "Missing datapoints are represented as null and never fabricated as 0.",
                "SQS ApproximateNumberOfMessagesVisible is an approximate metric and does not prove exact retry count.",
            ],
        }

    if cloudwatch_client is None:
        try:
            import boto3  # type: ignore
            from botocore.config import Config  # type: ignore
        except ModuleNotFoundError as exc:
            raise MetricsCollectionError("boto3 is required for live AWS CloudWatch execution.") from exc
        boto_cfg = Config(
            connect_timeout=5,
            read_timeout=10,
            retries={"total_max_attempts": 1, "max_attempts": 0, "mode": "standard"},
        )
        cloudwatch_client = boto3.client("cloudwatch", region_name=region, config=boto_cfg)

    records = []
    for spec in specs:
        try:
            call_now = datetime.now(timezone.utc)
            if (
                estimate_get_metric_statistics_datapoints(
                    resolved_start, resolved_end, period_seconds, now_utc=call_now
                )
                > 1440
            ):
                records.append(
                    {
                        **spec,
                        "periodSeconds": period_seconds,
                        "startTime": format_utc(resolved_start),
                        "endTime": format_utc(resolved_end),
                        "status": "API_ERROR",
                        "datapointCount": 0,
                        "latestValue": None,
                        "latestTimestamp": None,
                        "minValue": None,
                        "maxValue": None,
                        "meanValue": None,
                        "sumValue": None,
                        "errorCode": "DATAPOINT_LIMIT_EXCEEDED",
                        "note": "Skipped CloudWatch get_metric_statistics because current UTC age would exceed 1440 datapoints.",
                    }
                )
                continue
            response = cloudwatch_client.get_metric_statistics(
                Namespace=spec["namespace"],
                MetricName=spec["metricName"],
                Dimensions=[{"Name": spec["dimensionName"], "Value": spec["dimensionValue"]}],
                StartTime=resolved_start,
                EndTime=resolved_end,
                Period=period_seconds,
                Statistics=[spec["statistic"]],
            )
            datapoints = response.get("Datapoints", [])
            summary = summarize_datapoints(datapoints, spec["statistic"])
            records.append(
                {
                    **spec,
                    "periodSeconds": period_seconds,
                    "startTime": format_utc(resolved_start),
                    "endTime": format_utc(resolved_end),
                    **summary,
                    "errorCode": None,
                }
            )
        except Exception as exc:
            err_code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
            safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
            records.append(
                {
                    **spec,
                    "periodSeconds": period_seconds,
                    "startTime": format_utc(resolved_start),
                    "endTime": format_utc(resolved_end),
                    "status": "API_ERROR",
                    "datapointCount": 0,
                    "latestValue": None,
                    "latestTimestamp": None,
                    "minValue": None,
                    "maxValue": None,
                    "meanValue": None,
                    "sumValue": None,
                    "errorCode": safe_code,
                    "note": f"CloudWatch get_metric_statistics failed with {safe_code}.",
                }
            )

    alarms_summary = []
    if alarm_names:
        try:
            collected_alarms: List[Dict[str, Any]] = []
            next_token: Optional[str] = None
            page_count = 0
            while page_count < 10:
                page_count += 1
                desc_kwargs: Dict[str, Any] = {"AlarmNames": list(alarm_names)}
                if next_token:
                    desc_kwargs["NextToken"] = next_token
                alarm_resp = cloudwatch_client.describe_alarms(**desc_kwargs)
                for a in alarm_resp.get("MetricAlarms", []):
                    if isinstance(a, dict):
                        collected_alarms.append(a)
                next_token = alarm_resp.get("NextToken") if isinstance(alarm_resp, dict) else None
                if not next_token:
                    break

            found_by_name = {a.get("AlarmName"): a for a in collected_alarms}
            for name in alarm_names:
                alarm_obj = found_by_name.get(name)
                if not alarm_obj:
                    alarms_summary.append(
                        {
                            "alarmName": name,
                            "stateValue": "NOT_FOUND",
                            "metricName": None,
                            "namespace": None,
                            "updatedTimestamp": None,
                            "errorCode": None,
                        }
                    )
                else:
                    raw_updated = alarm_obj.get("StateUpdatedTimestamp")
                    updated_str: Optional[str] = None
                    if isinstance(raw_updated, datetime):
                        updated_str = format_utc(raw_updated)
                    elif isinstance(raw_updated, str) and raw_updated.strip():
                        try:
                            updated_str = format_utc(parse_utc_timestamp(raw_updated))
                        except MetricsCollectionError:
                            updated_str = None
                    alarms_summary.append(
                        {
                            "alarmName": name,
                            "stateValue": sanitize_text(alarm_obj.get("StateValue", "UNKNOWN"), 32),
                            "metricName": sanitize_text(alarm_obj.get("MetricName", ""), 64) or None,
                            "namespace": sanitize_text(alarm_obj.get("Namespace", ""), 64) or None,
                            "updatedTimestamp": updated_str,
                            "errorCode": None,
                        }
                    )
        except Exception as exc:
            err_code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
            safe_code = sanitize_text(err_code or exc.__class__.__name__, 64)
            for name in alarm_names:
                alarms_summary.append(
                    {
                        "alarmName": name,
                        "stateValue": "API_ERROR",
                        "metricName": None,
                        "namespace": None,
                        "updatedTimestamp": None,
                        "errorCode": safe_code,
                    }
                )

    return {
        "schemaVersion": "1.0",
        "sourceType": "CLOUDWATCH_METRICS",
        "runId": resolved_run_id,
        "collectedAt": format_utc(now_ts),
        "region": region,
        "windowStart": format_utc(resolved_start),
        "windowEnd": format_utc(resolved_end),
        "periodSeconds": period_seconds,
        "executeMode": True,
        "metrics": records,
        "alarms": alarms_summary,
        "limitations": [
            "Missing datapoints are kept as null and never replaced with 0 without measurement evidence.",
            "SQS ApproximateReceiveCount / ApproximateNumberOfMessagesVisible do not prove exact Lambda invocation counts.",
        ],
    }


def write_metrics_outputs(payload: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
    """Write JSON and CSV metric summaries to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cloudwatch-metrics-summary.json"
    csv_path = output_dir / "cloudwatch-metrics-results.csv"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fieldnames = [
        "runId",
        "resourceType",
        "resourceName",
        "namespace",
        "metricName",
        "statistic",
        "unit",
        "periodSeconds",
        "startTime",
        "endTime",
        "status",
        "datapointCount",
        "latestValue",
        "latestTimestamp",
        "minValue",
        "maxValue",
        "meanValue",
        "sumValue",
        "errorCode",
        "note",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload.get("metrics", []):
            writer.writerow({k: row.get(k) for k in fieldnames})

    return {"json": json_path, "csv": csv_path}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe CloudWatch monitoring & metrics collector (dry-run by default)."
    )
    parser.add_argument("--region", default="us-east-1", help="AWS Region (default: us-east-1).")
    parser.add_argument(
        "--queues",
        nargs="*",
        default=["orders-queue", "orders-dlq"],
        help="SQS queue names to inspect (default: orders-queue orders-dlq).",
    )
    parser.add_argument(
        "--functions",
        nargs="*",
        default=["order-producer", "order-consumer"],
        help="Lambda function names to inspect (default: order-producer order-consumer).",
    )
    parser.add_argument(
        "--alarms",
        nargs="*",
        default=["AsyncOrderProcessing-orders-dlq-VisibleMessages"],
        help="CloudWatch alarm names to inspect.",
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=30,
        help="Observation window in minutes when --start-time is omitted (default: 30).",
    )
    parser.add_argument("--start-time", help="Explicit UTC start time (ISO-8601).")
    parser.add_argument("--end-time", help="Explicit UTC end time (ISO-8601).")
    parser.add_argument(
        "--period",
        type=int,
        default=60,
        help="CloudWatch statistic period in seconds, multiple of 60 (default: 60).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory to write cloudwatch-metrics-summary.json and CSV.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run in offline dry-run mode without calling AWS (default when --execute is omitted).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Explicitly authorize read-only CloudWatch API calls in AWS Learner Lab.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.dry_run and args.execute:
            raise MetricsCollectionError("Conflicting flags: --dry-run and --execute cannot be used together.")
        if args.window_minutes <= 0 or args.window_minutes > 60 * 24 * 7:
            raise MetricsCollectionError("--window-minutes must be between 1 and 10080.")
        end_dt = parse_utc_timestamp(args.end_time) if args.end_time else datetime.now(timezone.utc).replace(microsecond=0)
        start_dt = (
            parse_utc_timestamp(args.start_time)
            if args.start_time
            else end_dt - timedelta(minutes=args.window_minutes)
        )

        payload = collect_cloudwatch_metrics(
            region=args.region,
            queues=args.queues,
            functions=args.functions,
            alarm_names=args.alarms,
            start_time=start_dt,
            end_time=end_dt,
            period_seconds=args.period,
            dry_run=bool(args.dry_run),
            execute=bool(args.execute),
        )
        if args.output_dir:
            write_metrics_outputs(payload, args.output_dir)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    except MetricsCollectionError as exc:
        print(json.dumps({"status": "ERROR", "error": sanitize_text(str(exc))}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
