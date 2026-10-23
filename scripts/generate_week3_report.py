"""Week 3 Performance & Observability Report Generator (W3-02, W3-03, W3-04).

Aggregates supplied JSON summaries from:
- SQS Standard vs FIFO benchmarks (scripts/benchmark_sqs.py)
- Controlled API load tests + DynamoDB reconciliation (scripts/load_test_orders.py)
- CloudWatch metrics & alarm snapshots (scripts/collect_cloudwatch_metrics.py)

Strictly preserves provenance for supplied inputs (e.g. SYNTHETIC_SAMPLE, DRY_RUN_PLAN,
or live execution sourceType) and omits sections whose input JSON is not supplied.
Missing numeric cells are rendered as an em dash (—) and never fabricated.
"""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence


class ReportGenerationError(Exception):
    """Error raised when input JSON files are malformed or invalid."""


def load_json_file(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        raise ReportGenerationError(f"Failed to load JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReportGenerationError(f"JSON root in {path} must be an object.")
    return data


def classify_provenance(payload: Optional[Dict[str, Any]], explicit_synthetic: bool = False) -> str:
    """Classify provenance of a supplied benchmark, load-test, or metrics summary."""
    if payload is None:
        return "—"
    if explicit_synthetic or payload.get("syntheticSample") is True or "SYNTHETIC" in str(payload.get("sourceType", "")).upper():
        return "SYNTHETIC_SAMPLE (MOCK / UNIT TEST)"
    if not payload.get("executeMode"):
        return "DRY_RUN_PLAN (NO LIVE AWS CALLS)"
    return str(payload.get("sourceType") or "AWS_EXECUTED_RUN")


def _fmt_val(val: Any, suffix: str = "") -> str:
    if val is None or val == "" or isinstance(val, bool):
        return "—"
    if isinstance(val, (int, float)) and not math.isfinite(float(val)):
        return "—"
    return f"{val}{suffix}"


def render_benchmark_comparison_table(
    runs: Sequence[Dict[str, Any]],
    explicit_synthetic: bool = False,
) -> str:
    """Render Markdown comparison table for supplied SQS Standard vs FIFO benchmark runs."""
    if not runs:
        return ""

    lines: List[str] = []
    has_synthetic = explicit_synthetic or any(
        "SYNTHETIC" in classify_provenance(r, explicit_synthetic) or not r.get("executeMode")
        for r in runs
    )
    if has_synthetic:
        lines.append("> [!WARNING]")
        lines.append("> **SYNTHETIC SAMPLE / DRY-RUN NOTICE:** Bảng dưới đây chứa dữ liệu `SYNTHETIC SAMPLE` hoặc `DRY-RUN` phục vụ kiểm thử công cụ offline, **KHÔNG PHẢI** số đo hiệu năng AWS thực tế.")
        lines.append("")

    lines.append(
        "| Run ID | Nguồn dữ liệu | Loại Queue | Groups | Messages (Sent/Fail/Unique/Dup) | Completeness | Send Throughput (msg/s) | Send Mean / P95 (ms) | Receive Poll Mean / P95 (ms) | Ordering Observation |"
    )
    lines.append("|---|---|---|---:|---|---:|---:|---|---|---|")

    for run in runs:
        prov = classify_provenance(run, explicit_synthetic)
        cfg = run.get("configuration", {})
        met = run.get("metrics", {})
        ord_info = run.get("ordering", {})
        send_lat = met.get("sendLatencyMs", {})
        recv_lat = met.get("receivePollLatencyMs", {})

        msg_summary = (
            f"{_fmt_val(met.get('acceptedSends'))}/{_fmt_val(met.get('failedSends'))}/"
            f"{_fmt_val(met.get('uniqueReceivedMessages'))}/{_fmt_val(met.get('duplicateObservations'))}"
        )
        comp = _fmt_val(met.get("receiveCompletenessRatio"))
        s_tput = _fmt_val(met.get("sendThroughputMsgPerSec"))
        s_lat = f"{_fmt_val(send_lat.get('meanMs'))} / {_fmt_val(send_lat.get('p95Ms'))}"
        r_lat = f"{_fmt_val(recv_lat.get('meanMs'))} / {_fmt_val(recv_lat.get('p95Ms'))}"

        all_in_order = ord_info.get("allGroupsInOrder")
        eval_groups = ord_info.get("evaluatedGroups")
        inversions = ord_info.get("totalOutOfOrderTransitions")
        if all_in_order is True and isinstance(eval_groups, int) and eval_groups > 0:
            ord_str = f"In-order ({eval_groups} group(s))"
        elif all_in_order is False and isinstance(eval_groups, int) and eval_groups > 0:
            ord_str = f"Out-of-order ({_fmt_val(inversions)} inversions)"
        else:
            ord_str = "—"

        lines.append(
            f"| `{_fmt_val(run.get('runId'))}` | `{prov}` | `{_fmt_val(cfg.get('queueType'))}` "
            f"| {_fmt_val(cfg.get('groupCount'))} | {msg_summary} | {comp} | {s_tput} | {s_lat} | {r_lat} | {ord_str} |"
        )

    return "\n".join(lines)


def render_load_test_section(
    load_summary: Optional[Dict[str, Any]],
    explicit_synthetic: bool = False,
) -> str:
    """Render Markdown summary for supplied W3-03 Controlled Load Test & DynamoDB Reconciliation."""
    if not load_summary:
        return ""

    prov = classify_provenance(load_summary, explicit_synthetic)
    cfg = load_summary.get("configuration") or {}
    summ = load_summary.get("summary") or {}
    rec = load_summary.get("reconciliation") or {}
    lat = summ.get("apiLatencyMs") or {}

    lines = [
        f"- **Run ID:** `{_fmt_val(load_summary.get('runId'))}`",
        f"- **Nguồn dữ liệu:** `{prov}`",
        f"- **Cấu hình:** `count={_fmt_val(cfg.get('requestCount'))}`, `rate={_fmt_val(cfg.get('rateLimitPerSec', ''), ' req/s')}`, `table={_fmt_val(cfg.get('tableName'))}`",
        f"- **Kết quả HTTP API:** Attempted `{_fmt_val(summ.get('requestsAttempted'))}`, HTTP 202 `{_fmt_val(summ.get('http202AcceptedCount'))}`, HTTP 400 `{_fmt_val(summ.get('http400Count'))}`, HTTP 429 `{_fmt_val(summ.get('http429Count'))}`, HTTP 5xx `{_fmt_val(summ.get('http5xxCount'))}`, Timeout `{_fmt_val(summ.get('timeoutCount'))}`",
        f"- **Độ trễ API (ms):** Mean `{_fmt_val(lat.get('meanMs'))}`, Median `{_fmt_val(lat.get('medianMs'))}`, P95 `{_fmt_val(lat.get('p95Ms'))}`",
    ]
    if rec:
        not_found_val = rec.get("notFoundCount")
        unverified_val = rec.get("unverifiedCount")
        pending_other_val = rec.get("pendingOrOtherStatusCount")
        valid_counts = [
            v
            for v in (not_found_val, unverified_val, pending_other_val)
            if isinstance(v, int) and not isinstance(v, bool)
        ]
        if len(valid_counts) == 3:
            remaining_str = str(sum(valid_counts))
        else:
            remaining_str = "—"
        lines.append(
            f"- **Đối soát DynamoDB (`GetItem`):** Trạng thái `{_fmt_val(rec.get('verificationStatus'))}`, "
            f"OrderIds `{_fmt_val(rec.get('orderIdsRequested'))}`, `PROCESSED = {_fmt_val(rec.get('processedCount'))}`, "
            f"Non-PROCESSED `{_fmt_val(pending_other_val)}`, Missing (`NOT_FOUND`) `{_fmt_val(not_found_val)}`, "
            f"Unverified `{_fmt_val(unverified_val)}`, Remaining `{remaining_str}`, "
            f"Thời gian đối soát `{_fmt_val(rec.get('reconciliationDurationSeconds'), 's')}`"
        )
    return "\n".join(lines)


def render_cloudwatch_section(
    cw_summary: Optional[Dict[str, Any]],
    explicit_synthetic: bool = False,
) -> str:
    """Render Markdown summary for supplied W3-01 / W3-04 CloudWatch metrics & alarms."""
    if not cw_summary:
        return ""

    prov = classify_provenance(cw_summary, explicit_synthetic)
    lines = [
        f"- **Run ID:** `{_fmt_val(cw_summary.get('runId'))}`",
        f"- **Nguồn dữ liệu:** `{prov}`",
        f"- **Khoảng quan sát (UTC):** `{_fmt_val(cw_summary.get('windowStart'))}` → `{_fmt_val(cw_summary.get('windowEnd'))}` (`period={_fmt_val(cw_summary.get('periodSeconds'), 's')}`)",
        "",
        "| Tài nguyên | Metric | Statistic | Status | Latest Value | Max Value | Mean / Sum | Ghi chú |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for item in cw_summary.get("metrics", []):
        agg_val = item.get("sumValue") if item.get("statistic") == "Sum" else item.get("meanValue")
        lines.append(
            f"| `{_fmt_val(item.get('resourceName'))}` | `{_fmt_val(item.get('metricName'))}` | `{_fmt_val(item.get('statistic'))}` "
            f"| `{_fmt_val(item.get('status'))}` | {_fmt_val(item.get('latestValue'))} | {_fmt_val(item.get('maxValue'))} "
            f"| {_fmt_val(agg_val)} | {item.get('note') or ''} |"
        )
    alarms = cw_summary.get("alarms")
    if isinstance(alarms, list) and alarms:
        lines.extend(
            [
                "",
                "| Alarm Name | State | Metric | Namespace | Updated (UTC) | Error Code |",
                "|---|---|---|---|---|---|",
            ]
        )
        for alarm in alarms:
            if isinstance(alarm, dict):
                lines.append(
                    f"| `{_fmt_val(alarm.get('alarmName'))}` | `{_fmt_val(alarm.get('stateValue'))}` "
                    f"| `{_fmt_val(alarm.get('metricName'))}` | `{_fmt_val(alarm.get('namespace'))}` "
                    f"| `{_fmt_val(alarm.get('updatedTimestamp'))}` | `{_fmt_val(alarm.get('errorCode'))}` |"
                )
    return "\n".join(lines)


def generate_markdown_report(
    *,
    benchmark_runs: Sequence[Dict[str, Any]] = (),
    load_summary: Optional[Dict[str, Any]] = None,
    cw_summary: Optional[Dict[str, Any]] = None,
    explicit_synthetic: bool = False,
) -> str:
    """Generate a Markdown report including only sections for supplied inputs."""
    now_str = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sections: List[str] = [
        "# Tổng hợp Kết quả Benchmark, Load Test và CloudWatch Metrics (Tuần 3)",
        "",
        f"- **Thời điểm tạo báo cáo (UTC):** `{now_str}`",
    ]
    if explicit_synthetic:
        sections.append("- **Nhãn dữ liệu:** `SYNTHETIC SAMPLE / OFFLINE TEST`")
    sections.append("")

    if benchmark_runs:
        sections.extend(
            [
                "## So sánh SQS Standard vs FIFO (SQS API Benchmark — W3-02)",
                "",
                render_benchmark_comparison_table(benchmark_runs, explicit_synthetic=explicit_synthetic),
                "",
                "### Giới hạn & Khuyến nghị kỹ thuật (Standard vs FIFO)",
                "- **Phân tách phạm vi đo:** SQS API benchmark chỉ đo độ trễ và thông lượng `SendMessage`/`ReceiveMessage` trực tiếp tới SQS, không bao gồm thời gian thực thi của `order-consumer` và `DynamoDB PutItem`.",
                "- **Ordering:** FIFO bảo đảm thứ tự trong từng `MessageGroupId` (`single-group` tuần tự hoàn toàn; `multi-group` tăng thông lượng song song theo nhóm nhưng các nhóm đan xen nhau). Standard là best-effort ordering.",
                "- **Deduplication vs Idempotency:** FIFO deduplication (5-minute window) chỉ ngăn gửi trùng ở tầng SQS Producer; nếu Consumer ghi DB xong nhưng gặp lỗi trước khi xóa message, message vẫn được nhận lại. Do đó cơ chế idempotency `attribute_not_exists(orderId)` ở Consumer vẫn bắt buộc cho cả Standard và FIFO.",
                "- **Khuyến nghị cho `cloud-async-orders`:** Giữ `orders-queue` (SQS Standard) kết hợp Consumer idempotency cho luồng đơn hàng chính để tối ưu thông lượng và đơn giản hóa Producer; sử dụng FIFO với `MessageGroupId = customerId` hoặc `orderId` khi nghiệp vụ yêu cầu tuần tự nghiêm ngặt các sự kiện trạng thái của cùng một đơn hàng/khách hàng.",
                "",
            ]
        )

    if load_summary:
        sections.extend(
            [
                "## Kiểm thử tải có kiểm soát & Đối soát DynamoDB (W3-03)",
                "",
                render_load_test_section(load_summary, explicit_synthetic=explicit_synthetic),
                "",
            ]
        )

    if cw_summary:
        sections.extend(
            [
                "## CloudWatch Metrics & Trạng thái Cảnh báo DLQ (W3-01 & W3-04)",
                "",
                render_cloudwatch_section(cw_summary, explicit_synthetic=explicit_synthetic),
                "",
            ]
        )

    return "\n".join(sections)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Markdown performance & observability summary from Week 3 JSON outputs."
    )
    parser.add_argument(
        "--benchmark-json",
        nargs="+",
        action="extend",
        type=Path,
        default=[],
        help="Path(s) to benchmark-summary.json files from scripts/benchmark_sqs.py.",
    )
    parser.add_argument(
        "--load-json",
        type=Path,
        help="Path to load-test-summary.json from scripts/load_test_orders.py.",
    )
    parser.add_argument(
        "--cloudwatch-json",
        type=Path,
        help="Path to cloudwatch-metrics-summary.json from scripts/collect_cloudwatch_metrics.py.",
    )
    parser.add_argument(
        "--synthetic-sample",
        action="store_true",
        help="Explicitly watermark the generated report as SYNTHETIC SAMPLE.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output Markdown file path.",
    )
    return parser


def _write_stdout_utf8_safe(text: str) -> None:
    """Write Unicode text to stdout without failing on narrow Windows codepages (e.g. cp1252)."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe_text = text.encode(enc, errors="replace").decode(enc, errors="replace")
        print(safe_text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        bench_runs = [load_json_file(p) for p in args.benchmark_json]
        load_data = load_json_file(args.load_json) if args.load_json else None
        cw_data = load_json_file(args.cloudwatch_json) if args.cloudwatch_json else None

        report_md = generate_markdown_report(
            benchmark_runs=bench_runs,
            load_summary=load_data,
            cw_summary=cw_data,
            explicit_synthetic=bool(args.synthetic_sample),
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report_md, encoding="utf-8")
        _write_stdout_utf8_safe(report_md)
        return 0
    except ReportGenerationError as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
