"""Offline unit tests for W3-02 SQS Standard vs FIFO Benchmark Tool.

Covers CLI arguments, conflicting --dry-run/--execute rejection, production queue
protection, FIFO .fifo naming and attributes, mock send success/failure, mock
receive/delete ownership verification (requiring matching accepted SQS MessageId),
honest rate sleep pacing, timeout & bounded polling, empty queue, duplicate
observation without inflating unique count, ordering validation, percentile
calculation, JSON/CSV generation, and AWS error handling.
"""

import csv
import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any, Dict, List
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
BENCH_PATH = ROOT_DIR / "scripts" / "benchmark_sqs.py"


def _load_bench():
    spec = importlib.util.spec_from_file_location("benchmark_sqs_under_test", BENCH_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bench = _load_bench()


class FakeSQSBenchmarkClient:
    """In-memory mock SQS client for deterministic offline benchmark tests."""

    def __init__(
        self,
        *,
        fail_send_seqs=(),
        fail_receive=False,
        duplicate_seq_deliveries=(),
        reverse_receive_order=False,
        empty_receive=False,
        preseeded_messages=None,
    ):
        self.fail_send_seqs = set(fail_send_seqs)
        self.fail_receive = fail_receive
        self.duplicate_seq_deliveries = set(duplicate_seq_deliveries)
        self.reverse_receive_order = reverse_receive_order
        self.empty_receive = empty_receive

        self.sent_calls: List[Dict[str, Any]] = []
        self.batch_calls: List[Dict[str, Any]] = []
        self.receive_calls: List[Dict[str, Any]] = []
        self.delete_calls: List[Dict[str, Any]] = []
        self.deleted_handles: List[str] = []
        self.get_queue_url_calls: List[str] = []
        self._queue: List[Dict[str, Any]] = list(preseeded_messages or [])
        self._prepared_for_receive = False

    def _require_canonical_queue_url(self, url: Any) -> None:
        if not isinstance(url, str) or not url.startswith("https://sqs.") or ".amazonaws.com/" not in url:
            raise AssertionError(f"SQS API requires full HTTPS QueueUrl, got: {url!r}")

    def get_queue_url(self, *, QueueName: str, **kwargs):
        self.get_queue_url_calls.append(QueueName)
        return {"QueueUrl": f"https://sqs.us-east-1.amazonaws.com/111122223333/{QueueName}"}

    def send_message(self, **kwargs):
        self._require_canonical_queue_url(kwargs.get("QueueUrl"))
        self.sent_calls.append(kwargs)
        body = json.loads(kwargs["MessageBody"])
        seq = body.get("sequenceNumber")
        if seq in self.fail_send_seqs:
            err = Exception("Simulated SendMessage error on 123456789012")
            err.response = {"Error": {"Code": "ServiceUnavailable"}}
            raise err

        msg_id = f"msg-{seq:04d}"
        attrs = {}
        if "MessageGroupId" in kwargs:
            attrs["MessageGroupId"] = kwargs["MessageGroupId"]
        msg_item = {
            "MessageId": msg_id,
            "ReceiptHandle": f"rh-{seq:04d}-1",
            "Body": kwargs["MessageBody"],
            "Attributes": attrs,
        }
        self._queue.append(msg_item)
        if seq in self.duplicate_seq_deliveries:
            dup_item = dict(msg_item)
            dup_item["ReceiptHandle"] = f"rh-{seq:04d}-2"
            self._queue.append(dup_item)
        return {"MessageId": msg_id}

    def send_message_batch(self, **kwargs):
        self._require_canonical_queue_url(kwargs.get("QueueUrl"))
        self.batch_calls.append(kwargs)
        successful = []
        failed = []
        for entry in kwargs.get("Entries", []):
            body = json.loads(entry["MessageBody"])
            seq = body.get("sequenceNumber")
            if seq in self.fail_send_seqs:
                failed.append({"Id": entry["Id"], "Code": "InternalError", "SenderFault": False})
            else:
                msg_id = f"batch-msg-{seq:04d}"
                successful.append({"Id": entry["Id"], "MessageId": msg_id})
                self._queue.append(
                    {
                        "MessageId": msg_id,
                        "ReceiptHandle": f"rh-batch-{seq:04d}",
                        "Body": entry["MessageBody"],
                        "Attributes": {"MessageGroupId": entry.get("MessageGroupId", "default")},
                    }
                )
        return {"Successful": successful, "Failed": failed}

    def receive_message(self, **kwargs):
        self._require_canonical_queue_url(kwargs.get("QueueUrl"))
        self.receive_calls.append(kwargs)
        if self.fail_receive:
            err = Exception("Simulated ReceiveMessage error")
            err.response = {"Error": {"Code": "RequestThrottled"}}
            raise err
        if self.empty_receive:
            return {"Messages": []}
        if not self._prepared_for_receive:
            self._prepared_for_receive = True
            if self.reverse_receive_order:
                self._queue.reverse()
        max_msgs = kwargs.get("MaxNumberOfMessages", 1)
        batch = self._queue[:max_msgs]
        self._queue = self._queue[max_msgs:]
        return {"Messages": batch}

    def delete_message(self, **kwargs):
        self._require_canonical_queue_url(kwargs.get("QueueUrl"))
        self.delete_calls.append(kwargs)
        self.deleted_handles.append(kwargs.get("ReceiptHandle", ""))
        return {}


class TestBenchmarkSqs(unittest.TestCase):
    def test_cli_arguments_and_dry_run_default_and_conflicting_flags(self):
        parser = bench.build_arg_parser()
        args = parser.parse_args(
            [
                "--queue-type",
                "fifo",
                "--queue-url",
                "https://sqs.us-east-1.amazonaws.com/111122223333/orders-benchmark.fifo",
                "--message-count",
                "12",
                "--group-count",
                "3",
            ]
        )
        self.assertEqual(args.queue_type, "fifo")
        self.assertEqual(args.message_count, 12)
        self.assertEqual(args.group_count, 3)
        self.assertFalse(args.execute)

        res = bench.run_sqs_benchmark(
            queue_type="fifo",
            queue_url="https://sqs.us-east-1.amazonaws.com/111122223333/orders-benchmark.fifo",
            message_count=12,
            group_count=3,
            execute=False,
        )
        self.assertFalse(res["executeMode"])
        self.assertEqual(res["sourceType"], "DRY_RUN_PLAN")
        self.assertTrue(res["sampleMessagePreview"]["hasMessageGroupId"])
        self.assertTrue(res["sampleMessagePreview"]["hasMessageDeduplicationId"])

        # Conflicting --dry-run and --execute must fail before any SDK call
        with self.assertRaises(bench.BenchmarkError):
            bench.run_sqs_benchmark(
                queue_type="standard",
                queue_url="orders-benchmark-standard",
                dry_run=True,
                execute=True,
                confirm_target="orders-benchmark-standard",
            )
        exit_code = bench.main(
            [
                "--queue-type",
                "standard",
                "--queue-url",
                "orders-benchmark-standard",
                "--dry-run",
                "--execute",
                "--confirm-target",
                "orders-benchmark-standard",
            ]
        )
        self.assertEqual(exit_code, 2)

    def test_protected_production_queues_and_invalid_configs_rejected(self):
        for prod_q in (
            "orders-queue",
            "orders-dlq",
            "https://sqs.us-east-1.amazonaws.com/111122223333/orders-queue",
            "https://sqs.us-east-1.amazonaws.com/111122223333/orders-dlq",
        ):
            with self.subTest(prod_q=prod_q):
                with self.assertRaises(bench.BenchmarkError):
                    bench.run_sqs_benchmark(queue_type="standard", queue_url=prod_q, execute=False)

        with self.assertRaises(bench.BenchmarkError):
            bench.run_sqs_benchmark(queue_type="fifo", queue_url="orders-benchmark-standard", execute=False)

        with self.assertRaises(bench.BenchmarkError):
            bench.run_sqs_benchmark(queue_type="standard", queue_url="orders-benchmark.fifo", execute=False)

        # Reject malformed SQS URLs with query/fragment or non-12-digit account segment
        for bad_url in (
            "https://sqs.us-east-1.amazonaws.com/not12digits/orders-benchmark-standard",
            "https://sqs.us-east-1.amazonaws.com/111122223333/extra/orders-benchmark-standard",
            "https://sqs.us-east-1.amazonaws.com/111122223333/orders-benchmark-standard?foo=bar",
            "https://sqs.us-east-1.amazonaws.com/111122223333/orders-benchmark-standard#frag",
        ):
            with self.subTest(bad_url=bad_url):
                with self.assertRaises(bench.BenchmarkError):
                    bench.run_sqs_benchmark(queue_type="standard", queue_url=bad_url, execute=False)

        # Reject NaN / Inf rates
        for bad_rate in (float("nan"), float("inf"), -1.0, 0.0):
            with self.subTest(bad_rate=bad_rate):
                with self.assertRaises(bench.BenchmarkError):
                    bench.run_sqs_benchmark(
                        queue_type="standard",
                        queue_url="orders-benchmark-standard",
                        rate_limit=bad_rate,
                        execute=False,
                    )

        with self.assertRaises(bench.BenchmarkError):
            bench.run_sqs_benchmark(
                queue_type="standard",
                queue_url="orders-benchmark-standard",
                execute=True,
                confirm_target="wrong-name",
            )

    def test_fifo_single_and_multi_group_attributes_and_rate_pacing(self):
        client = FakeSQSBenchmarkClient()
        sleeps: List[float] = []
        res = bench.run_sqs_benchmark(
            queue_type="fifo",
            queue_url="orders-benchmark.fifo",
            message_count=3,
            group_count=2,
            rate_limit=0.5,  # 2.0 seconds per message (must not be capped at 0.2s)
            dedup_mode="explicit",
            execute=True,
            confirm_target="orders-benchmark.fifo",
            sqs_client=client,
            run_id="run-fifo-01",
            sleep_fn=sleeps.append,
        )
        self.assertEqual(res["metrics"]["acceptedSends"], 3)
        self.assertEqual(res["metrics"]["uniqueReceivedMessages"], 3)
        self.assertEqual(res["metrics"]["duplicateObservations"], 0)
        self.assertEqual(res["metrics"]["receiveCompletenessRatio"], 1.0)
        self.assertTrue(res["ordering"]["allGroupsInOrder"])
        self.assertEqual(res["ordering"]["evaluatedGroups"], 2)
        self.assertEqual(len(client.deleted_handles), 3)
        self.assertEqual(sleeps, [2.0, 2.0])

        for call in client.sent_calls:
            self.assertIn("MessageGroupId", call)
            self.assertIn("MessageDeduplicationId", call)

    def test_delete_ownership_requires_matching_accepted_sqs_message_id(self):
        # Spoofed/stale message in queue with the same runId and orderId, but a different SQS MessageId
        spoofed_msg = {
            "MessageId": "foreign-sqs-msg-9999",
            "ReceiptHandle": "rh-foreign-do-not-delete",
            "Body": json.dumps(
                {
                    "benchmarkRunId": "reused-run-id",
                    "sequenceNumber": 1,
                    "messageGroupId": "bench-group-01",
                    "orderId": "BENCH-reused-run-id-0001",
                }
            ),
            "Attributes": {},
        }
        client = FakeSQSBenchmarkClient(preseeded_messages=[spoofed_msg])
        res = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=1,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=client,
            run_id="reused-run-id",
            sleep_fn=lambda _: None,
        )
        # Only the genuinely accepted message (msg-0001 / rh-0001-1) may be counted and deleted
        self.assertEqual(res["metrics"]["acceptedSends"], 1)
        self.assertEqual(res["metrics"]["uniqueReceivedMessages"], 1)
        self.assertEqual(res["metrics"]["duplicateObservations"], 0)
        self.assertEqual(client.deleted_handles, ["rh-0001-1"])
        self.assertNotIn("rh-foreign-do-not-delete", client.deleted_handles)

    def test_duplicate_observation_and_out_of_order_detection(self):
        client = FakeSQSBenchmarkClient(
            fail_send_seqs={5},
            duplicate_seq_deliveries={2},
            reverse_receive_order=True,
        )
        res = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=5,
            batch_size=1,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=client,
            run_id="run-std-dup",
            sleep_fn=lambda _: None,
        )
        self.assertEqual(res["metrics"]["attemptedMessages"], 5)
        self.assertEqual(res["metrics"]["acceptedSends"], 4)
        self.assertEqual(res["metrics"]["failedSends"], 1)
        self.assertEqual(res["metrics"]["uniqueReceivedMessages"], 4)
        self.assertEqual(res["metrics"]["duplicateObservations"], 1)
        self.assertFalse(res["ordering"]["allGroupsInOrder"])
        self.assertGreater(res["ordering"]["totalOutOfOrderTransitions"], 0)

    def test_batch_send_timeout_empty_queue_and_receive_error(self):
        empty_client = FakeSQSBenchmarkClient(empty_receive=True)
        res_empty = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=4,
            batch_size=2,
            max_polls=3,
            timeout_seconds=10.0,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=empty_client,
            run_id="run-empty",
            sleep_fn=lambda _: None,
        )
        self.assertEqual(res_empty["metrics"]["acceptedSends"], 4)
        self.assertEqual(res_empty["metrics"]["uniqueReceivedMessages"], 0)
        self.assertEqual(res_empty["metrics"]["pollsExecuted"], 3)

        err_client = FakeSQSBenchmarkClient(fail_receive=True)
        res_err = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=2,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=err_client,
            run_id="run-recv-err",
            sleep_fn=lambda _: None,
        )
        self.assertEqual(res_err["metrics"]["acceptedSends"], 2)
        self.assertEqual(res_err["metrics"]["uniqueReceivedMessages"], 0)
        self.assertTrue(any(r["status"] == "POLL_ERROR" for r in res_err["records"]))

    def test_percentile_calculation_and_json_csv_outputs(self):
        stats = bench.compute_latency_stats([10.0, 20.0, 30.0, 40.0, 100.0])
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["minMs"], 10.0)
        self.assertEqual(stats["maxMs"], 100.0)
        self.assertEqual(stats["meanMs"], 40.0)
        self.assertEqual(stats["medianMs"], 30.0)
        self.assertEqual(stats["p95Ms"], 100.0)

        client = FakeSQSBenchmarkClient()
        res = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=3,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=client,
            run_id="run-out-01",
            sleep_fn=lambda _: None,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = bench.write_benchmark_outputs(res, Path(tmpdir))
            self.assertTrue(paths["json"].exists())
            self.assertTrue(paths["csv"].exists())
            loaded_json = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(loaded_json["runId"], "run-out-01")
            with paths["csv"].open("r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 6)

    def test_boto_config_disables_hidden_retries_and_deadline_stops_poll_and_delete(self):
        cfg_short = bench.build_bounded_boto_config(0.25)
        self.assertEqual(cfg_short.connect_timeout, 0.25)
        self.assertEqual(cfg_short.read_timeout, 0.25)
        self.assertEqual(cfg_short.retries.get("total_max_attempts"), 1)
        self.assertEqual(cfg_short.retries.get("max_attempts"), 0)

        cfg_long = bench.build_bounded_boto_config(25.0)
        self.assertEqual(cfg_long.connect_timeout, 10.0)
        self.assertEqual(cfg_long.read_timeout, 10.0)
        self.assertEqual(cfg_long.retries.get("total_max_attempts"), 1)

        # Clock-advancing stub: receive_message advances clock past deadline so delete_message and next poll are skipped
        now = [100.0]

        def clock_fn() -> float:
            return now[0]

        class ClockAdvancingSQSClient:
            def __init__(self):
                self.receive_calls = 0
                self.delete_calls = 0

            def get_queue_url(self, *, QueueName: str, **kwargs):
                return {"QueueUrl": f"https://sqs.us-east-1.amazonaws.com/111122223333/{QueueName}"}

            def send_message(self, **kwargs):
                now[0] += 0.01
                return {"MessageId": "msg-deadline-01"}

            def receive_message(self, **kwargs):
                self.receive_calls += 1
                # Advance clock past the 0.5s receive deadline during the in-flight receive
                now[0] += 0.60
                return {
                    "Messages": [
                        {
                            "MessageId": "msg-deadline-01",
                            "ReceiptHandle": "rh-deadline-01",
                            "Body": json.dumps(
                                {
                                    "benchmarkRunId": "run-deadline-01",
                                    "sequenceNumber": 1,
                                    "messageGroupId": "bench-group-01",
                                    "orderId": "BENCH-run-deadline-01-0001",
                                }
                            ),
                            "Attributes": {},
                        }
                    ]
                }

            def delete_message(self, **kwargs):
                self.delete_calls += 1
                return {}

        slow_client = ClockAdvancingSQSClient()
        res = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=1,
            timeout_seconds=0.5,
            max_polls=5,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=slow_client,
            run_id="run-deadline-01",
            clock_fn=clock_fn,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(slow_client.receive_calls, 1)
        self.assertEqual(slow_client.delete_calls, 0)
        self.assertEqual(res["metrics"]["pollsExecuted"], 1)

    def test_bare_queue_name_resolves_canonical_queue_url_before_sqs_operations(self):
        client = FakeSQSBenchmarkClient()
        res = bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url="orders-benchmark-standard",
            message_count=2,
            batch_size=1,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=client,
            run_id="run-bare-url-01",
            sleep_fn=lambda _: None,
        )
        expected_url = "https://sqs.us-east-1.amazonaws.com/111122223333/orders-benchmark-standard"
        self.assertEqual(client.get_queue_url_calls, ["orders-benchmark-standard"])
        self.assertEqual(res["metrics"]["acceptedSends"], 2)
        self.assertEqual(res["metrics"]["uniqueReceivedMessages"], 2)
        self.assertTrue(all(c["QueueUrl"] == expected_url for c in client.sent_calls))
        self.assertTrue(all(c["QueueUrl"] == expected_url for c in client.receive_calls))
        self.assertTrue(all(c["QueueUrl"] == expected_url for c in client.delete_calls))

        # Full QueueUrl input must not call get_queue_url
        full_url_client = FakeSQSBenchmarkClient()
        bench.run_sqs_benchmark(
            queue_type="standard",
            queue_url=expected_url,
            message_count=1,
            execute=True,
            confirm_target="orders-benchmark-standard",
            sqs_client=full_url_client,
            run_id="run-full-url-01",
            sleep_fn=lambda _: None,
        )
        self.assertEqual(full_url_client.get_queue_url_calls, [])

        # Invalid or mismatched get_queue_url responses must fail before any send_message call
        class MismatchedGetQueueUrlClient(FakeSQSBenchmarkClient):
            def get_queue_url(self, *, QueueName: str, **kwargs):
                return {"QueueUrl": "https://sqs.us-east-1.amazonaws.com/111122223333/other-queue"}

        bad_client = MismatchedGetQueueUrlClient()
        with self.assertRaises(bench.BenchmarkError):
            bench.run_sqs_benchmark(
                queue_type="standard",
                queue_url="orders-benchmark-standard",
                message_count=1,
                execute=True,
                confirm_target="orders-benchmark-standard",
                sqs_client=bad_client,
                sleep_fn=lambda _: None,
            )
        self.assertEqual(bad_client.sent_calls, [])


if __name__ == "__main__":
    unittest.main()
