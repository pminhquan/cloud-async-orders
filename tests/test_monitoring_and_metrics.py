"""Offline unit tests for W3-01 CloudWatch Monitoring IaC & W3-04 Metrics Collector.

Verifies CloudFormation template structure/parameters/dimensions/actions/region-rules
without live AWS calls, and tests collect_cloudwatch_metrics.py and generate_week3_report.py
across valid, missing-data, missing-timestamp, conflicting-flags, API-error, invalid-config,
and secret-redaction paths.
"""

from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
IAC_PATH = ROOT_DIR / "iac" / "week3-monitoring.yaml"
COLLECTOR_PATH = ROOT_DIR / "scripts" / "collect_cloudwatch_metrics.py"
REPORT_GEN_PATH = ROOT_DIR / "scripts" / "generate_week3_report.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_cfn_yaml(path: Path):
    """Parse CloudFormation YAML supporting intrinsic tags (!Ref, !Sub, !Equals, !And, !Condition)."""

    class CfnLoader(yaml.SafeLoader):
        pass

    def _make_constructor(tag_name):
        def _construct_intrinsic(loader, node):
            if isinstance(node, yaml.ScalarNode):
                val = loader.construct_scalar(node)
            elif isinstance(node, yaml.SequenceNode):
                val = loader.construct_sequence(node)
            else:
                val = loader.construct_mapping(node)
            return {f"!{tag_name}": val}

        return _construct_intrinsic

    for tag in ("Ref", "Sub", "Equals", "If", "Not", "And", "Or", "GetAtt", "Condition"):
        CfnLoader.add_constructor(f"!{tag}", _make_constructor(tag))

    return yaml.load(path.read_text(encoding="utf-8"), Loader=CfnLoader)


collector_mod = _load_module("collect_cloudwatch_metrics_under_test", COLLECTOR_PATH)
report_mod = _load_module("generate_week3_report_under_test", REPORT_GEN_PATH)


class FakeCloudWatchClient:
    """Deterministic offline mock for CloudWatch get_metric_statistics and describe_alarms."""

    def __init__(self, datapoints_by_metric=None, alarms=None, fail_metrics=False, fail_alarms=False):
        self.datapoints_by_metric = datapoints_by_metric or {}
        self.alarms = alarms or []
        self.fail_metrics = fail_metrics
        self.fail_alarms = fail_alarms
        self.calls = []

    def get_metric_statistics(self, **kwargs):
        self.calls.append(("get_metric_statistics", kwargs))
        if self.fail_metrics:
            err = Exception("Simulated CloudWatch error for 123456789012 AKIAIOSFODNN7EXAMPLE")
            err.response = {"Error": {"Code": "ThrottlingException"}}
            raise err
        key = (kwargs["Namespace"], kwargs["MetricName"], kwargs["Dimensions"][0]["Value"])
        return {"Datapoints": self.datapoints_by_metric.get(key, [])}

    def describe_alarms(self, **kwargs):
        self.calls.append(("describe_alarms", kwargs))
        if self.fail_alarms:
            err = Exception("AccessDenied on 123456789012")
            err.response = {"Error": {"Code": "AccessDenied"}}
            raise err
        return {"MetricAlarms": self.alarms}


class TestMonitoringAndMetrics(unittest.TestCase):
    def test_cloudformation_template_valid_and_compliant(self):
        self.assertTrue(IAC_PATH.exists(), "iac/week3-monitoring.yaml must exist")
        raw_text = IAC_PATH.read_text(encoding="utf-8")

        # Must not hard-code 12-digit AWS account IDs or personal ARNs
        self.assertIsNone(re.search(r"\b[0-9]{12}\b", raw_text))
        self.assertNotIn("AWS::IAM::Role", raw_text)
        self.assertNotIn("AWS::IAM::User", raw_text)
        self.assertNotIn("AWS::SNS::Topic", raw_text)

        tpl = _load_cfn_yaml(IAC_PATH)
        self.assertEqual(tpl["AWSTemplateFormatVersion"], "2010-09-09")

        params = tpl["Parameters"]
        for required_param in (
            "AWSRegionName",
            "MainQueueName",
            "DLQName",
            "AlertSnsTopicArn",
            "DLQAlarmThreshold",
            "DLQEvaluationPeriods",
            "ProjectTag",
            "OwnerTag",
        ):
            self.assertIn(required_param, params)

        self.assertEqual(params["DLQName"]["Default"], "orders-dlq")
        self.assertEqual(params["MainQueueName"]["Default"], "orders-queue")
        self.assertEqual(params["DLQAlarmThreshold"]["Default"], 1)

        # Enforce region consistency against AWS::Region
        self.assertIn("Rules", tpl)
        self.assertIn("EnforceMatchingStackRegion", tpl["Rules"])
        self.assertIn("RegionMatchesStack", tpl["Conditions"])

        resources = tpl["Resources"]
        self.assertIn("DLQVisibleMessagesAlarm", resources)
        dlq_alarm = resources["DLQVisibleMessagesAlarm"]
        self.assertEqual(dlq_alarm["Type"], "AWS::CloudWatch::Alarm")
        props = dlq_alarm["Properties"]
        self.assertEqual(props["Namespace"], "AWS/SQS")
        self.assertEqual(props["MetricName"], "ApproximateNumberOfMessagesVisible")
        self.assertEqual(props["Dimensions"], [{"Name": "QueueName", "Value": {"!Ref": "DLQName"}}])
        self.assertEqual(props["ComparisonOperator"], "GreaterThanOrEqualToThreshold")
        self.assertEqual(props["Threshold"], {"!Ref": "DLQAlarmThreshold"})
        self.assertEqual(props["TreatMissingData"], "notBreaching")
        self.assertEqual(props["AlarmActions"], [{"!Ref": "AlertSnsTopicArn"}])

    def test_collector_dry_run_default_and_conflicting_flags_rejected(self):
        start_t = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
        end_t = datetime(2026, 10, 23, 12, 30, 0, tzinfo=timezone.utc)
        res = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            queues=["orders-queue", "orders-dlq"],
            functions=["order-producer", "order-consumer"],
            alarm_names=["AsyncOrderProcessing-orders-dlq-VisibleMessages"],
            start_time=start_t,
            end_time=end_t,
            period_seconds=60,
            execute=False,
        )
        self.assertFalse(res["executeMode"])
        self.assertEqual(res["sourceType"], "DRY_RUN_PLAN")
        self.assertTrue(all(m["latestValue"] is None for m in res["metrics"]))
        self.assertTrue(all(m["status"] == "DRY_RUN_NOT_EXECUTED" for m in res["metrics"]))

        # Conflicting --dry-run and --execute must fail before any SDK client creation
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1",
                start_time=start_t,
                end_time=end_t,
                dry_run=True,
                execute=True,
            )
        exit_code = collector_mod.main(["--dry-run", "--execute"])
        self.assertEqual(exit_code, 2)

    def test_collector_parses_datapoints_and_rejects_missing_timestamps(self):
        start_t = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
        end_t = datetime(2026, 10, 23, 12, 30, 0, tzinfo=timezone.utc)
        dp_map = {
            ("AWS/SQS", "ApproximateNumberOfMessagesVisible", "orders-dlq"): [
                {"Timestamp": datetime(2026, 10, 23, 12, 5, 0, tzinfo=timezone.utc), "Maximum": 0.0, "Unit": "Count"},
                {"Timestamp": datetime(2026, 10, 23, 12, 10, 0, tzinfo=timezone.utc), "Maximum": 2.0, "Unit": "Count"},
            ],
            ("AWS/Lambda", "Errors", "order-consumer"): [
                {"Timestamp": datetime(2026, 10, 23, 12, 10, 0, tzinfo=timezone.utc), "Sum": 1.0, "Unit": "Count"},
            ],
            # Datapoint without Timestamp must NEVER be assigned datetime.now()
            ("AWS/Lambda", "Throttles", "order-consumer"): [
                {"Sum": 3.0, "Unit": "Count"},
            ],
        }
        alarms = [
            {
                "AlarmName": "AsyncOrderProcessing-orders-dlq-VisibleMessages",
                "StateValue": "ALARM",
                "MetricName": "ApproximateNumberOfMessagesVisible",
                "Namespace": "AWS/SQS",
                "StateUpdatedTimestamp": datetime(2026, 10, 23, 12, 11, 0, tzinfo=timezone.utc),
            }
        ]
        client = FakeCloudWatchClient(datapoints_by_metric=dp_map, alarms=alarms)
        res = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            queues=["orders-dlq"],
            functions=["order-consumer"],
            alarm_names=["AsyncOrderProcessing-orders-dlq-VisibleMessages", "MissingAlarm"],
            start_time=start_t,
            end_time=end_t,
            period_seconds=60,
            execute=True,
            cloudwatch_client=client,
        )

        by_metric = {(m["resourceName"], m["metricName"], m["statistic"]): m for m in res["metrics"]}
        dlq_vis = by_metric[("orders-dlq", "ApproximateNumberOfMessagesVisible", "Maximum")]
        self.assertEqual(dlq_vis["status"], "OK")
        self.assertEqual(dlq_vis["latestValue"], 2.0)
        self.assertEqual(dlq_vis["maxValue"], 2.0)

        # Missing datapoint metric must remain null, never fabricated as 0
        dlq_age = by_metric[("orders-dlq", "ApproximateAgeOfOldestMessage", "Maximum")]
        self.assertEqual(dlq_age["status"], "NO_DATA")
        self.assertIsNone(dlq_age["latestValue"])
        self.assertIsNone(dlq_age["meanValue"])

        # Datapoint without Timestamp must report INVALID_DATAPOINTS and null latestTimestamp
        throttles = by_metric[("order-consumer", "Throttles", "Sum")]
        self.assertEqual(throttles["status"], "INVALID_DATAPOINTS")
        self.assertIsNone(throttles["latestValue"])
        self.assertIsNone(throttles["latestTimestamp"])

        alarm_states = {a["alarmName"]: a["stateValue"] for a in res["alarms"]}
        self.assertEqual(alarm_states["AsyncOrderProcessing-orders-dlq-VisibleMessages"], "ALARM")
        self.assertEqual(alarm_states["MissingAlarm"], "NOT_FOUND")

        # Verify describe_alarms pagination and string StateUpdatedTimestamp normalization
        class PaginatedAlarmClient(FakeCloudWatchClient):
            def describe_alarms(self, **kwargs):
                self.calls.append(("describe_alarms", kwargs))
                if not kwargs.get("NextToken"):
                    return {
                        "MetricAlarms": [
                            {
                                "AlarmName": "AlarmPage1",
                                "StateValue": "OK",
                                "MetricName": "ApproximateNumberOfMessagesVisible",
                                "Namespace": "AWS/SQS",
                                "StateUpdatedTimestamp": "2026-10-23T12:15:00+00:00",
                            }
                        ],
                        "NextToken": "token-page-2",
                    }
                return {
                    "MetricAlarms": [
                        {
                            "AlarmName": "AlarmPage2",
                            "StateValue": "ALARM",
                            "MetricName": "Errors",
                            "Namespace": "AWS/Lambda",
                            "StateUpdatedTimestamp": "not-an-iso-timestamp",
                        }
                    ]
                }

        paged_client = PaginatedAlarmClient()
        res_paged = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            queues=["orders-dlq"],
            functions=[],
            alarm_names=["AlarmPage1", "AlarmPage2"],
            start_time=start_t,
            end_time=end_t,
            period_seconds=60,
            execute=True,
            cloudwatch_client=paged_client,
        )
        paged_alarms = {a["alarmName"]: a for a in res_paged["alarms"]}
        self.assertEqual(paged_alarms["AlarmPage1"]["stateValue"], "OK")
        self.assertEqual(paged_alarms["AlarmPage1"]["updatedTimestamp"], "2026-10-23T12:15:00Z")
        self.assertEqual(paged_alarms["AlarmPage2"]["stateValue"], "ALARM")
        self.assertIsNone(paged_alarms["AlarmPage2"]["updatedTimestamp"])

    def test_collector_handles_api_errors_and_redacts_secrets_and_writes_files(self):
        start_t = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
        end_t = datetime(2026, 10, 23, 12, 30, 0, tzinfo=timezone.utc)
        client = FakeCloudWatchClient(fail_metrics=True, fail_alarms=True)

        res = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            queues=["orders-dlq"],
            functions=["order-consumer"],
            alarm_names=["AsyncOrderProcessing-orders-dlq-VisibleMessages"],
            start_time=start_t,
            end_time=end_t,
            period_seconds=60,
            execute=True,
            cloudwatch_client=client,
        )
        serialized = json.dumps(res)
        self.assertNotIn("123456789012", serialized)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", serialized)
        self.assertTrue(all(m["status"] == "API_ERROR" for m in res["metrics"]))
        self.assertEqual(res["alarms"][0]["stateValue"], "API_ERROR")

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = collector_mod.write_metrics_outputs(res, Path(tmpdir))
            self.assertTrue(paths["json"].exists())
            self.assertTrue(paths["csv"].exists())

    def test_collector_invalid_configuration_rejected(self):
        start_t = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
        end_t = datetime(2026, 10, 23, 12, 30, 0, tzinfo=timezone.utc)

        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="eu-central-1", start_time=start_t, end_time=end_t
            )
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1", queues=[], functions=[], start_time=start_t, end_time=end_t
            )
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1", period_seconds=45, start_time=start_t, end_time=end_t
            )
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1", start_time=end_t, end_time=start_t
            )
        # Window > 1440 datapoints (e.g., 2 days at period=60s -> 2880 datapoints) must be rejected
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1",
                period_seconds=60,
                start_time=datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc),
            )
        # Exactly 1440 datapoints (24h aligned at period=60s) is allowed
        res_1440 = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            period_seconds=60,
            start_time=datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc),
            execute=False,
        )
        self.assertEqual(res_1440["periodSeconds"], 60)
        # Aligned recent start to +24h - 1s (spans 1440 buckets with exclusive EndTime) is allowed
        res_24h_minus_1s = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            period_seconds=60,
            start_time=datetime(2026, 10, 21, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 10, 21, 23, 59, 59, tzinfo=timezone.utc),
            execute=False,
        )
        self.assertEqual(res_24h_minus_1s["periodSeconds"], 60)
        # Unaligned recent start (12:00:01) ending at aligned 1440 boundary (+24h from 12:00:00) is allowed
        res_unaligned_aligned_end = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            period_seconds=60,
            start_time=datetime(2026, 10, 22, 12, 0, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc),
            execute=False,
        )
        self.assertEqual(res_unaligned_aligned_end["periodSeconds"], 60)
        # One-slot / partial-slot overflow (24h + 1s aligned start -> 1441 slots) rejected before SDK call
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1",
                period_seconds=60,
                start_time=datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 10, 23, 12, 0, 1, tzinfo=timezone.utc),
                execute=False,
            )
        # Unaligned start (12:00:01 to +24h at period=60s -> AWS rounds start down to 12:00:00 -> 1441 slots) rejected before SDK call
        unaligned_client = FakeCloudWatchClient()
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.collect_cloudwatch_metrics(
                region="us-east-1",
                period_seconds=60,
                start_time=datetime(2026, 10, 22, 12, 0, 1, tzinfo=timezone.utc),
                end_time=datetime(2026, 10, 23, 12, 0, 1, tzinfo=timezone.utc),
                execute=True,
                cloudwatch_client=unaligned_client,
            )
        self.assertEqual(unaligned_client.calls, [])
        # Verify helper age-based StartTime floor grids (5-minute for 15..63d, 1-hour for >63d) with fixed now_utc
        fixed_now = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
        # 20 days ago (15..63d -> 5-minute StartTime floor): 12:04:00 floors to 12:00:00 -> +24h from 12:04:00 is 1444 slots at 60s
        self.assertEqual(
            collector_mod.estimate_get_metric_statistics_datapoints(
                datetime(2026, 10, 3, 12, 4, 0, tzinfo=timezone.utc),
                datetime(2026, 10, 4, 12, 4, 0, tzinfo=timezone.utc),
                60,
                now_utc=fixed_now,
            ),
            1444,
        )
        # 70 days ago (>63d -> 1-hour StartTime floor): 12:59:00 floors to 12:00:00 -> +24h from 12:59:00 is 1499 slots at 60s
        self.assertEqual(
            collector_mod.estimate_get_metric_statistics_datapoints(
                datetime(2026, 8, 10, 12, 59, 0, tzinfo=timezone.utc),
                datetime(2026, 8, 11, 12, 59, 0, tzinfo=timezone.utc),
                60,
                now_utc=fixed_now,
            ),
            1499,
        )
        # Reachable 15-day threshold crossing case (5-day window within 7-day cap, Period=300):
        # start 2026-10-09T12:04:00Z, end 2026-10-14T12:04:00Z -> conservatively 1441 on both sides of 2026-10-24T12:04:00Z
        s_15d = datetime(2026, 10, 9, 12, 4, 0, tzinfo=timezone.utc)
        e_15d = datetime(2026, 10, 14, 12, 4, 0, tzinfo=timezone.utc)
        for boundary_now in (
            datetime(2026, 10, 24, 12, 3, 59, 900000, tzinfo=timezone.utc),
            datetime(2026, 10, 24, 12, 4, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 24, 12, 4, 0, 100000, tzinfo=timezone.utc),
        ):
            with self.subTest(boundary_now=boundary_now.isoformat()):
                self.assertEqual(
                    collector_mod.estimate_get_metric_statistics_datapoints(
                        s_15d, e_15d, 300, now_utc=boundary_now
                    ),
                    1441,
                )
                boundary_client = FakeCloudWatchClient()
                with self.assertRaises(collector_mod.MetricsCollectionError):
                    collector_mod.collect_cloudwatch_metrics(
                        region="us-east-1",
                        period_seconds=300,
                        start_time=s_15d,
                        end_time=e_15d,
                        execute=True,
                        cloudwatch_client=boundary_client,
                        now_utc=boundary_now,
                    )
                self.assertEqual(boundary_client.calls, [])
        # Outside the 5-minute receipt safety margin before 15d (e.g. 10 minutes before 15d), normal <15d behavior (1440) is preserved
        safe_before_15d = datetime(2026, 10, 24, 11, 50, 0, tzinfo=timezone.utc)
        self.assertEqual(
            collector_mod.estimate_get_metric_statistics_datapoints(
                s_15d, e_15d, 300, now_utc=safe_before_15d
            ),
            1440,
        )
        # 5-minute-aligned start (2026-10-09T12:00:00Z to 2026-10-14T12:00:00Z) stays <= 1440 even across the 15-day boundary
        res_aligned_15d = collector_mod.collect_cloudwatch_metrics(
            region="us-east-1",
            period_seconds=300,
            start_time=datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc),
            execute=False,
            now_utc=datetime(2026, 10, 24, 11, 59, 59, 900000, tzinfo=timezone.utc),
        )
        self.assertEqual(res_aligned_15d["periodSeconds"], 300)
        # 63-day pure-helper boundary crossing case (start 2026-08-22T12:05:00Z, end 2026-10-21T12:05:00Z, Period=3600):
        s_63d = datetime(2026, 8, 22, 12, 5, 0, tzinfo=timezone.utc)
        e_63d = datetime(2026, 10, 21, 12, 5, 0, tzinfo=timezone.utc)
        for boundary_now_63d in (
            datetime(2026, 10, 24, 12, 4, 59, 900000, tzinfo=timezone.utc),
            datetime(2026, 10, 24, 12, 5, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 24, 12, 5, 0, 100000, tzinfo=timezone.utc),
        ):
            with self.subTest(boundary_now_63d=boundary_now_63d.isoformat()):
                self.assertEqual(
                    collector_mod.estimate_get_metric_statistics_datapoints(
                        s_63d, e_63d, 3600, now_utc=boundary_now_63d
                    ),
                    1441,
                )
        with self.assertRaises(collector_mod.MetricsCollectionError):
            collector_mod.parse_utc_timestamp("not-a-timestamp")

        # Sequential per-request guard test: initially safe 15d/Period=300 window crosses into unsafe (>1440) mid-loop
        # First metric call succeeds at 11:58:00Z (1440 datapoints); clock advances to 12:00:00Z so remaining 5 metric calls are blocked
        clock_state = {"now": datetime(2026, 10, 24, 11, 58, 0, tzinfo=timezone.utc)}

        class FakeDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock_state["now"]

        class ClockAdvancingCloudWatchClient(FakeCloudWatchClient):
            def get_metric_statistics(self, **kwargs):
                res = super().get_metric_statistics(**kwargs)
                # Advance clock into the 5-minute receipt margin (11:59:00Z..12:04:00Z) after first metric request completes
                clock_state["now"] = datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc)
                return res

        seq_dp = {
            ("AWS/SQS", "ApproximateNumberOfMessagesVisible", "orders-dlq"): [
                {"Timestamp": "2026-10-14T12:00:00Z", "Maximum": 4.0, "Unit": "Count"}
            ]
        }
        seq_client = ClockAdvancingCloudWatchClient(datapoints_by_metric=seq_dp)
        with patch.object(collector_mod, "datetime", FakeDateTime):
            res_seq = collector_mod.collect_cloudwatch_metrics(
                region="us-east-1",
                queues=["orders-dlq"],
                functions=[],
                alarm_names=[],
                start_time=s_15d,
                end_time=e_15d,
                period_seconds=300,
                execute=True,
                cloudwatch_client=seq_client,
                now_utc=datetime(2026, 10, 24, 11, 50, 0, tzinfo=timezone.utc),
            )
        # Only the first metric call was sent to AWS SDK; remaining 5 SQS metrics were blocked pre-request
        self.assertEqual(len(seq_client.calls), 1)
        self.assertEqual(res_seq["metrics"][0]["metricName"], "ApproximateNumberOfMessagesVisible")
        self.assertEqual(res_seq["metrics"][0]["status"], "OK")
        self.assertEqual(res_seq["metrics"][0]["latestValue"], 4.0)
        for skipped_m in res_seq["metrics"][1:]:
            self.assertEqual(skipped_m["status"], "API_ERROR")
            self.assertEqual(skipped_m["errorCode"], "DATAPOINT_LIMIT_EXCEEDED")
            self.assertIsNone(skipped_m["latestValue"])
            self.assertIsNone(skipped_m["minValue"])
            self.assertIsNone(skipped_m["maxValue"])
            self.assertIsNone(skipped_m["meanValue"])
            self.assertIsNone(skipped_m["sumValue"])

    def test_report_generator_omits_absent_sections_and_watermarks_synthetic_or_dryrun(self):
        md_empty = report_mod.generate_markdown_report()
        self.assertIn("# Tổng hợp Kết quả Benchmark, Load Test và CloudWatch Metrics (Tuần 3)", md_empty)
        self.assertNotIn("VERIFIED PROVENANCE MODE", md_empty)
        self.assertNotIn("PENDING", md_empty.upper())
        self.assertNotIn("Chưa chạy", md_empty)
        self.assertNotIn("Chưa đo", md_empty)
        self.assertNotIn("So sánh SQS Standard vs FIFO", md_empty)
        self.assertNotIn("Kiểm thử tải có kiểm soát", md_empty)
        self.assertNotIn("CloudWatch Metrics & Trạng thái Cảnh báo DLQ", md_empty)

        fake_bench = {
            "runId": "synth-01",
            "executeMode": False,
            "syntheticSample": True,
            "sourceType": "SYNTHETIC_SAMPLE",
            "configuration": {"queueType": "fifo", "groupCount": 1},
            "metrics": {
                "acceptedSends": 10,
                "failedSends": 0,
                "uniqueReceivedMessages": 10,
                "duplicateObservations": 0,
                "receiveCompletenessRatio": 1.0,
                "sendThroughputMsgPerSec": 25.0,
                "sendLatencyMs": {"meanMs": 12.5, "p95Ms": 18.0},
                "receivePollLatencyMs": {"meanMs": 15.0, "p95Ms": 22.0},
            },
            "ordering": {"allGroupsInOrder": True, "evaluatedGroups": 1},
        }
        md_synth = report_mod.generate_markdown_report(
            benchmark_runs=[fake_bench],
            explicit_synthetic=True,
        )
        self.assertIn("SYNTHETIC SAMPLE", md_synth)
        self.assertIn("synth-01", md_synth)
        self.assertIn("So sánh SQS Standard vs FIFO", md_synth)
        self.assertNotIn("Kiểm thử tải có kiểm soát", md_synth)
        self.assertNotIn("CloudWatch Metrics & Trạng thái Cảnh báo DLQ", md_synth)
        self.assertNotIn("VERIFIED PROVENANCE MODE", md_synth)
        self.assertNotIn("PENDING", md_synth.upper())

        fake_load = {
            "runId": "load-only-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "configuration": {"requestCount": 5, "rateLimitPerSec": 1.0, "tableName": "Orders"},
            "summary": {
                "requestsAttempted": 5,
                "http202AcceptedCount": 0,
                "http400Count": 0,
                "http429Count": 0,
                "http5xxCount": 0,
                "timeoutCount": 0,
                "apiLatencyMs": {"meanMs": None, "medianMs": None, "p95Ms": None},
            },
            "reconciliation": {
                "verificationStatus": "DRY_RUN_NOT_EXECUTED",
                "orderIdsRequested": 0,
                "processedCount": 0,
                "notFoundCount": 0,
                "unverifiedCount": 0,
                "reconciliationDurationSeconds": None,
            },
        }
        md_load_only = report_mod.generate_markdown_report(load_summary=fake_load)
        self.assertIn("Kiểm thử tải có kiểm soát", md_load_only)
        self.assertIn("load-only-01", md_load_only)
        self.assertIn("—", md_load_only)
        self.assertNotIn("So sánh SQS Standard vs FIFO", md_load_only)
        self.assertNotIn("CloudWatch Metrics & Trạng thái Cảnh báo DLQ", md_load_only)
        self.assertNotIn("VERIFIED PROVENANCE MODE", md_load_only)
        self.assertNotIn("PENDING", md_load_only.upper())

        fake_cw = {
            "runId": "cw-only-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "windowStart": "2026-10-23T09:30:00Z",
            "windowEnd": "2026-10-23T10:00:00Z",
            "periodSeconds": 60,
            "metrics": [
                {
                    "resourceName": "orders-dlq",
                    "metricName": "ApproximateNumberOfMessagesVisible",
                    "statistic": "Maximum",
                    "status": "NO_DATA",
                    "latestValue": None,
                    "maxValue": None,
                    "meanValue": None,
                    "sumValue": None,
                    "note": "No datapoints",
                }
            ],
            "alarms": [
                {
                    "alarmName": "AsyncOrderProcessing-orders-dlq-VisibleMessages",
                    "stateValue": "ALARM",
                    "metricName": "ApproximateNumberOfMessagesVisible",
                    "namespace": "AWS/SQS",
                    "updatedTimestamp": "2026-10-23T09:55:00Z",
                    "errorCode": None,
                }
            ],
        }
        md_cw_only = report_mod.generate_markdown_report(cw_summary=fake_cw)
        self.assertIn("CloudWatch Metrics & Trạng thái Cảnh báo DLQ", md_cw_only)
        self.assertIn("cw-only-01", md_cw_only)
        self.assertIn("AsyncOrderProcessing-orders-dlq-VisibleMessages", md_cw_only)
        self.assertIn("| `AsyncOrderProcessing-orders-dlq-VisibleMessages` | `ALARM` |", md_cw_only)
        self.assertIn("—", md_cw_only)
        self.assertNotIn("So sánh SQS Standard vs FIFO", md_cw_only)
        self.assertNotIn("Kiểm thử tải có kiểm soát", md_cw_only)
        self.assertNotIn("VERIFIED PROVENANCE MODE", md_cw_only)
        self.assertNotIn("PENDING", md_cw_only.upper())

    def test_report_generator_sparse_inputs_do_not_invent_zeros_or_none_status(self):
        sparse_bench = {
            "runId": "sparse-bench-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "configuration": {"queueType": "standard"},
            "metrics": {},
            "ordering": {"allGroupsInOrder": True, "evaluatedGroups": 0},
        }
        sparse_load = {
            "runId": "sparse-load-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "configuration": {},
            "summary": {"http202AcceptedCount": 0},
            "reconciliation": {"notFoundCount": 2},
        }
        md_sparse = report_mod.generate_markdown_report(
            benchmark_runs=[sparse_bench],
            load_summary=sparse_load,
        )
        # Missing benchmark counts must be em dashes (—/—/—/—), never invented 0/0/0/0
        self.assertIn("—/—/—/—", md_sparse)
        self.assertNotIn("0/0/0/0", md_sparse)
        # Ordering with evaluatedGroups=0 must not be labeled In-order or Out-of-order
        self.assertNotIn("In-order", md_sparse)
        self.assertNotIn("Out-of-order", md_sparse)
        # Real zero (HTTP 202 `0`) is kept, while missing counts are `—` and never `None`
        self.assertIn("Attempted `—`, HTTP 202 `0`, HTTP 400 `—`, HTTP 429 `—`, HTTP 5xx `—`, Timeout `—`", md_sparse)
        self.assertIn(
            "Trạng thái `—`, OrderIds `—`, `PROCESSED = —`, Non-PROCESSED `—`, Missing (`NOT_FOUND`) `2`, Unverified `—`, Remaining `—`",
            md_sparse,
        )
        self.assertNotIn("None", md_sparse)
        self.assertIn("DRY_RUN_PLAN (NO LIVE AWS CALLS)", md_sparse)

        # Sparse input with exactly two known reconciliation categories (third missing/invalid) must render Remaining as `—`
        sparse_two_load = {
            "runId": "sparse-two-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "configuration": {},
            "summary": {"http202AcceptedCount": 2},
            "reconciliation": {"notFoundCount": 1, "unverifiedCount": 1},
        }
        md_sparse_two = report_mod.generate_markdown_report(load_summary=sparse_two_load)
        self.assertIn(
            "Non-PROCESSED `—`, Missing (`NOT_FOUND`) `1`, Unverified `1`, Remaining `—`",
            md_sparse_two,
        )

        # Verify explicit reconciliation breakdown counts in generated report
        full_rec_load = {
            "runId": "rec-breakdown-01",
            "executeMode": True,
            "sourceType": "CONTROLLED_API_LOAD_TEST",
            "configuration": {"requestCount": 5, "rateLimitPerSec": 2.0, "tableName": "Orders"},
            "summary": {"requestsAttempted": 5, "http202AcceptedCount": 5},
            "reconciliation": {
                "verificationStatus": "PARTIALLY_PROCESSED",
                "orderIdsRequested": 5,
                "processedCount": 2,
                "pendingOrOtherStatusCount": 1,
                "notFoundCount": 1,
                "unverifiedCount": 1,
                "reconciliationDurationSeconds": 1.25,
            },
        }
        md_rec = report_mod.generate_markdown_report(load_summary=full_rec_load)
        self.assertIn(
            "OrderIds `5`, `PROCESSED = 2`, Non-PROCESSED `1`, Missing (`NOT_FOUND`) `1`, Unverified `1`, Remaining `3`, Thời gian đối soát `1.25s`",
            md_rec,
        )

    def test_report_cli_handles_cp1252_stdout_and_writes_utf8_output_file(self):
        fake_bench_std = {
            "runId": "dry-std-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "configuration": {"queueType": "standard", "groupCount": 0},
            "metrics": {
                "acceptedSends": 0,
                "failedSends": 0,
                "uniqueReceivedMessages": 0,
                "duplicateObservations": 0,
                "receiveCompletenessRatio": None,
                "sendThroughputMsgPerSec": None,
                "sendLatencyMs": {"meanMs": None, "p95Ms": None},
                "receivePollLatencyMs": {"meanMs": None, "p95Ms": None},
            },
            "ordering": {"allGroupsInOrder": None, "evaluatedGroups": 0},
        }
        fake_bench_fifo = {
            "runId": "dry-fifo-01",
            "executeMode": False,
            "sourceType": "DRY_RUN_PLAN",
            "configuration": {"queueType": "fifo", "groupCount": 1},
            "metrics": {
                "acceptedSends": 0,
                "failedSends": 0,
                "uniqueReceivedMessages": 0,
                "duplicateObservations": 0,
                "receiveCompletenessRatio": None,
                "sendThroughputMsgPerSec": None,
                "sendLatencyMs": {"meanMs": None, "p95Ms": None},
                "receivePollLatencyMs": {"meanMs": None, "p95Ms": None},
            },
            "ordering": {"allGroupsInOrder": None, "evaluatedGroups": 0},
        }

        class StrictCp1252Stdout:
            encoding = "cp1252"

            def __init__(self):
                self.chunks = []

            def write(self, s: str) -> int:
                s.encode("cp1252", errors="strict")
                self.chunks.append(s)
                return len(s)

            def flush(self) -> None:
                pass

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            b1 = tmp_path / "bench-std.json"
            b2 = tmp_path / "bench-fifo.json"
            out_md = tmp_path / "report-out.md"
            b1.write_text(json.dumps(fake_bench_std), encoding="utf-8")
            b2.write_text(json.dumps(fake_bench_fifo), encoding="utf-8")

            strict_stdout = StrictCp1252Stdout()
            with patch.object(sys, "stdout", strict_stdout):
                exit_code = report_mod.main(
                    [
                        "--benchmark-json",
                        str(b1),
                        "--benchmark-json",
                        str(b2),
                        "--output",
                        str(out_md),
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertTrue(out_md.exists())
            written_text = out_md.read_text(encoding="utf-8")
            self.assertIn("Tổng hợp Kết quả Benchmark, Load Test và CloudWatch Metrics (Tuần 3)", written_text)
            self.assertIn("dry-std-01", written_text)
            self.assertIn("dry-fifo-01", written_text)

            out_sub = tmp_path / "report-sub.md"
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "cp1252"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(REPORT_GEN_PATH),
                    "--benchmark-json",
                    str(b1),
                    "--benchmark-json",
                    str(b2),
                    "--output",
                    str(out_sub),
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr.decode("utf-8", errors="replace"))
            self.assertTrue(out_sub.exists())
            sub_text = out_sub.read_text(encoding="utf-8")
            self.assertIn("Tổng hợp Kết quả Benchmark, Load Test và CloudWatch Metrics (Tuần 3)", sub_text)
            self.assertIn("dry-std-01", sub_text)
            self.assertIn("dry-fifo-01", sub_text)
            self.assertIn("DRY_RUN_PLAN (NO LIVE AWS CALLS)", sub_text)
            self.assertIn("—", sub_text)
            self.assertNotIn("VERIFIED PROVENANCE MODE", sub_text)
            self.assertNotIn("PENDING", sub_text.upper())
            self.assertNotIn("Chưa đo", sub_text)
            self.assertNotIn("Kiểm thử tải có kiểm soát", sub_text)
            self.assertNotIn("CloudWatch Metrics & Trạng thái Cảnh báo DLQ", sub_text)


if __name__ == "__main__":
    unittest.main()
