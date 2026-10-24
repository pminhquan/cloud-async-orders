"""Offline unit tests for W3-03 Controlled Load Test & DynamoDB Reconciliation Tool.

Covers API 202 success, conflicting --dry-run/--execute rejection, finite rate
validation & uncapped sleep pacing, invalid/malformed responses, missing orderId,
HTTP 400/429/500, request timeouts, rate-limit bounds, DynamoDB eventual visibility
via GetItem, query timeout, access denied handling, and JSON/CSV output generation
without live AWS calls.
"""

import csv
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
from typing import Any, Dict, List, Tuple
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
LOAD_PATH = ROOT_DIR / "scripts" / "load_test_orders.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("load_test_orders_under_test", LOAD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


load_tool = _load_tool()


class FakeEventualDynamoDBTable:
    """In-memory mock DynamoDB table supporting eventual visibility and access errors."""

    def __init__(self, visible_on_attempt: Dict[str, Tuple[int, str]], raise_access_denied: bool = False):
        self.visible_on_attempt = dict(visible_on_attempt)
        self.raise_access_denied = raise_access_denied
        self.attempts_by_key: Dict[str, int] = {}
        self.get_calls: List[Dict[str, Any]] = []

    def get_item(self, Key: Dict[str, Any], ConsistentRead: bool = False) -> Dict[str, Any]:
        self.get_calls.append({"Key": Key, "ConsistentRead": ConsistentRead})
        if self.raise_access_denied:
            err = Exception("AccessDeniedException on 123456789012")
            err.response = {"Error": {"Code": "AccessDeniedException"}}
            raise err
        oid = Key["orderId"]
        attempt = self.attempts_by_key.get(oid, 0) + 1
        self.attempts_by_key[oid] = attempt
        if oid in self.visible_on_attempt:
            min_attempt, status_val = self.visible_on_attempt[oid]
            if attempt >= min_attempt:
                return {"Item": {"orderId": oid, "status": status_val}}
        return {}


class TestLoadTestOrders(unittest.TestCase):
    def test_dry_run_default_and_config_validation_and_conflicting_flags(self):
        endpoint = "https://example-api.execute-api.us-east-1.amazonaws.com/orders"
        res = load_tool.run_controlled_load_test(
            endpoint=endpoint,
            request_count=5,
            rate_limit=2.0,
            execute=False,
        )
        self.assertFalse(res["executeMode"])
        self.assertEqual(res["sourceType"], "DRY_RUN_PLAN")
        self.assertEqual(res["reconciliation"]["verificationStatus"], "DRY_RUN_NOT_EXECUTED")

        # Conflicting --dry-run and --execute must fail before any HTTP/AWS call
        with self.assertRaises(load_tool.LoadTestError):
            load_tool.run_controlled_load_test(
                endpoint=endpoint,
                dry_run=True,
                execute=True,
                confirm_target="example-api.execute-api.us-east-1.amazonaws.com",
            )
        exit_code = load_tool.main(
            [
                "--endpoint",
                endpoint,
                "--dry-run",
                "--execute",
                "--confirm-target",
                "example-api.execute-api.us-east-1.amazonaws.com",
            ]
        )
        self.assertEqual(exit_code, 2)

        # Missing or non-https endpoint rejected
        with self.assertRaises(load_tool.LoadTestError):
            load_tool.run_controlled_load_test(endpoint="", execute=False)
        with self.assertRaises(load_tool.LoadTestError):
            load_tool.run_controlled_load_test(endpoint="http://insecure.example.com/orders", execute=False)

        # Rate > 10 req/s or non-finite rate rejected
        for bad_rate in (15.0, 0.0, -2.0, float("nan"), float("inf")):
            with self.subTest(bad_rate=bad_rate):
                with self.assertRaises(load_tool.LoadTestError):
                    load_tool.run_controlled_load_test(endpoint=endpoint, rate_limit=bad_rate, execute=False)

        # Unbounded request count (> 100) rejected
        with self.assertRaises(load_tool.LoadTestError):
            load_tool.run_controlled_load_test(endpoint=endpoint, request_count=500, execute=False)

        # Execute without matching --confirm-target rejected
        with self.assertRaises(load_tool.LoadTestError):
            load_tool.run_controlled_load_test(
                endpoint=endpoint,
                execute=True,
                confirm_target="wrong-host.example.com",
            )

    def test_mixed_api_responses_rate_pacing_and_eventual_dynamodb_reconciliation(self):
        endpoint = "https://example-api.execute-api.us-east-1.amazonaws.com/orders"
        host = "example-api.execute-api.us-east-1.amazonaws.com"

        call_counter = {"n": 0}

        def fake_post(url: str, payload: Dict[str, Any], timeout: float) -> Tuple[int, str]:
            call_counter["n"] += 1
            idx = call_counter["n"]
            if idx == 1:
                return 202, json.dumps({"message": "Order accepted", "order": {"orderId": "ORD-1", "status": "PENDING"}})
            if idx == 2:
                return 202, json.dumps({"message": "Order accepted", "order": {"orderId": "ORD-2", "status": "PENDING"}})
            if idx == 3:
                return 202, json.dumps({"message": "Order accepted", "order": {"orderId": "ORD-3", "status": "PENDING"}})
            if idx == 4:
                return 202, json.dumps({"message": "Order accepted", "order": {}})
            if idx == 5:
                return 202, "{not-valid-json"
            if idx == 6:
                return 429, json.dumps({"message": "Too Many Requests"})
            raise socket.timeout("timed out")

        fake_table = FakeEventualDynamoDBTable(
            visible_on_attempt={
                "ORD-1": (1, "PROCESSED"),
                "ORD-2": (2, "PROCESSED"),
                "ORD-3": (1, "PENDING"),
            }
        )

        sleeps: List[float] = []
        res = load_tool.run_controlled_load_test(
            endpoint=endpoint,
            request_count=7,
            rate_limit=0.5,  # 2.0s interval between requests (must not be capped at 1.0s)
            timeout_seconds=2.0,
            reconcile=True,
            reconcile_timeout=10.0,
            reconcile_max_polls=3,
            execute=True,
            confirm_target=host,
            http_post_fn=fake_post,
            dynamodb_table=fake_table,
            run_id="load-run-01",
            sleep_fn=sleeps.append,
        )

        # First 6 inter-request sleeps must be 2.0s each
        self.assertEqual(sleeps[:6], [2.0] * 6)

        summ = res["summary"]
        self.assertEqual(summ["requestsAttempted"], 7)
        self.assertEqual(summ["http202AcceptedCount"], 5)
        self.assertEqual(summ["orderIdsCollectedCount"], 3)
        self.assertEqual(summ["missingOrderIdOn202Count"], 1)
        self.assertEqual(summ["malformed202ResponseCount"], 1)
        self.assertEqual(summ["http429Count"], 1)
        self.assertEqual(summ["timeoutCount"], 1)

        rec = res["reconciliation"]
        self.assertEqual(rec["verificationStatus"], "PARTIALLY_PROCESSED")
        self.assertEqual(rec["orderIdsRequested"], 3)
        self.assertEqual(rec["processedCount"], 2)
        self.assertEqual(rec["pendingOrOtherStatusCount"], 1)
        self.assertTrue(all(c["ConsistentRead"] for c in fake_table.get_calls))

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = load_tool.write_load_test_outputs(res, Path(tmpdir))
            self.assertTrue(paths["json"].exists())
            self.assertTrue(paths["csv"].exists())
            with paths["csv"].open("r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 7)

    def test_dynamodb_access_denied_and_query_timeout_reported_honestly(self):
        denied_table = FakeEventualDynamoDBTable({}, raise_access_denied=True)
        rec_denied = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-10", "ORD-11"],
            table_name="Orders",
            dynamodb_table=denied_table,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(rec_denied["verificationStatus"], "UNVERIFIED_DYNAMODB_ACCESS_ERROR")
        self.assertEqual(rec_denied["processedCount"], 0)
        self.assertEqual(rec_denied["unverifiedCount"], 2)

        empty_table = FakeEventualDynamoDBTable({})
        rec_timeout = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-NEVER"],
            table_name="Orders",
            timeout_seconds=1.0,
            max_polls=2,
            dynamodb_table=empty_table,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(rec_timeout["verificationStatus"], "NONE_PROCESSED_WITHIN_TIMEOUT")
        self.assertEqual(rec_timeout["processedCount"], 0)
        self.assertEqual(rec_timeout["notFoundCount"], 1)
        self.assertEqual(rec_timeout["pollsExecuted"], 2)

        class MixedThenAccessDeniedTable:
            def get_item(self, Key: Dict[str, Any], ConsistentRead: bool = False) -> Dict[str, Any]:
                oid = Key["orderId"]
                if oid == "ORD-DONE":
                    return {"Item": {"orderId": oid, "status": "PROCESSED"}}
                if oid == "ORD-PEND":
                    return {"Item": {"orderId": oid, "status": "PENDING"}}
                if oid == "ORD-MISS":
                    return {}
                err = Exception("AccessDeniedException")
                err.response = {"Error": {"Code": "AccessDeniedException"}}
                raise err

        rec_mixed_denied = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-DONE", "ORD-PEND", "ORD-MISS", "ORD-DENIED", "ORD-UNREACHED"],
            table_name="Orders",
            dynamodb_table=MixedThenAccessDeniedTable(),
            sleep_fn=lambda _: None,
        )
        self.assertEqual(rec_mixed_denied["verificationStatus"], "UNVERIFIED_DYNAMODB_ACCESS_ERROR")
        self.assertEqual(rec_mixed_denied["processedCount"], 1)
        self.assertEqual(rec_mixed_denied["pendingOrOtherStatusCount"], 1)
        self.assertEqual(rec_mixed_denied["notFoundCount"], 1)
        self.assertEqual(rec_mixed_denied["unverifiedCount"], 2)
        self.assertEqual(rec_mixed_denied["perOrder"]["ORD-PEND"]["state"], "NON_PROCESSED_STATUS")
        self.assertEqual(rec_mixed_denied["perOrder"]["ORD-MISS"]["state"], "NOT_FOUND_YET")
        self.assertEqual(rec_mixed_denied["perOrder"]["ORD-DENIED"]["state"], "UNVERIFIED_ACCESS_DENIED")
        self.assertEqual(rec_mixed_denied["perOrder"]["ORD-UNREACHED"]["state"], "UNVERIFIED_ACCESS_DENIED")

        # Repeat-poll regression: order observed PENDING or missing on pass 1, then SAME order gets AccessDenied on pass 2
        class SecondPassAccessDeniedTable:
            def __init__(self, first_pass_item: Dict[str, Any]):
                self.first_pass_item = first_pass_item
                self.calls = 0

            def get_item(self, Key: Dict[str, Any], ConsistentRead: bool = False) -> Dict[str, Any]:
                self.calls += 1
                if self.calls == 1:
                    return self.first_pass_item
                err = Exception("AccessDeniedException")
                err.response = {"Error": {"Code": "AccessDeniedException"}}
                raise err

        rec_pend_then_denied = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-SAME-PEND"],
            table_name="Orders",
            max_polls=3,
            dynamodb_table=SecondPassAccessDeniedTable({"Item": {"orderId": "ORD-SAME-PEND", "status": "PENDING"}}),
            sleep_fn=lambda _: None,
        )
        self.assertEqual(rec_pend_then_denied["verificationStatus"], "UNVERIFIED_DYNAMODB_ACCESS_ERROR")
        self.assertEqual(rec_pend_then_denied["perOrder"]["ORD-SAME-PEND"]["state"], "NON_PROCESSED_STATUS")
        self.assertEqual(rec_pend_then_denied["pendingOrOtherStatusCount"], 1)
        self.assertEqual(rec_pend_then_denied["notFoundCount"], 0)
        self.assertEqual(rec_pend_then_denied["unverifiedCount"], 0)
        self.assertEqual(
            rec_pend_then_denied["processedCount"]
            + rec_pend_then_denied["pendingOrOtherStatusCount"]
            + rec_pend_then_denied["notFoundCount"]
            + rec_pend_then_denied["unverifiedCount"],
            rec_pend_then_denied["orderIdsRequested"],
        )

        rec_miss_then_denied = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-SAME-MISS"],
            table_name="Orders",
            max_polls=3,
            dynamodb_table=SecondPassAccessDeniedTable({}),
            sleep_fn=lambda _: None,
        )
        self.assertEqual(rec_miss_then_denied["verificationStatus"], "UNVERIFIED_DYNAMODB_ACCESS_ERROR")
        self.assertEqual(rec_miss_then_denied["perOrder"]["ORD-SAME-MISS"]["state"], "NOT_FOUND_YET")
        self.assertEqual(rec_miss_then_denied["pendingOrOtherStatusCount"], 0)
        self.assertEqual(rec_miss_then_denied["notFoundCount"], 1)
        self.assertEqual(rec_miss_then_denied["unverifiedCount"], 0)
        self.assertEqual(
            rec_miss_then_denied["processedCount"]
            + rec_miss_then_denied["pendingOrOtherStatusCount"]
            + rec_miss_then_denied["notFoundCount"]
            + rec_miss_then_denied["unverifiedCount"],
            rec_miss_then_denied["orderIdsRequested"],
        )

        # Evidence test 1: reconcile=False marks collected orderIds as unverified without any DynamoDB reads
        no_read_table = FakeEventualDynamoDBTable({"ORD-NR-1": (1, "PROCESSED"), "ORD-NR-2": (1, "PROCESSED")})
        nr_counter = {"n": 0}

        def fake_post_nr(url: str, payload: Dict[str, Any], timeout: float) -> Tuple[int, str]:
            nr_counter["n"] += 1
            return 202, json.dumps({"order": {"orderId": f"ORD-NR-{nr_counter['n']}", "status": "PENDING"}})

        res_no_reconcile = load_tool.run_controlled_load_test(
            endpoint="https://example-api.execute-api.us-east-1.amazonaws.com/orders",
            request_count=2,
            rate_limit=2.0,
            reconcile=False,
            execute=True,
            confirm_target="example-api.execute-api.us-east-1.amazonaws.com",
            http_post_fn=fake_post_nr,
            dynamodb_table=no_read_table,
            sleep_fn=lambda _: None,
        )
        rec_disabled = res_no_reconcile["reconciliation"]
        self.assertEqual(rec_disabled["verificationStatus"], "RECONCILIATION_DISABLED")
        self.assertEqual(rec_disabled["orderIdsRequested"], 2)
        self.assertEqual(rec_disabled["processedCount"], 0)
        self.assertEqual(rec_disabled["pendingOrOtherStatusCount"], 0)
        self.assertEqual(rec_disabled["notFoundCount"], 0)
        self.assertEqual(rec_disabled["unverifiedCount"], 2)
        self.assertEqual(rec_disabled["pollsExecuted"], 0)
        self.assertEqual(no_read_table.get_calls, [])
        self.assertTrue(all(r["reconciledState"] == "NOT_CHECKED" for r in res_no_reconcile["requests"]))

        # Evidence test 2: ResourceNotFoundException classifies as QUERY_ERROR / unverified (not missing or pending)
        class ResourceNotFoundDynamoTable:
            def __init__(self):
                self.calls = 0

            def get_item(self, Key: Dict[str, Any], ConsistentRead: bool = False) -> Dict[str, Any]:
                self.calls += 1
                err = Exception("Requested resource not found: Table: Orders not found")
                err.response = {"Error": {"Code": "ResourceNotFoundException"}}
                raise err

        rnf_table = ResourceNotFoundDynamoTable()
        rec_rnf = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-RNF-1", "ORD-RNF-2"],
            table_name="Orders",
            max_polls=2,
            dynamodb_table=rnf_table,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(rec_rnf["verificationStatus"], "UNVERIFIED")
        self.assertEqual(rec_rnf["orderIdsRequested"], 2)
        self.assertEqual(rec_rnf["processedCount"], 0)
        self.assertEqual(rec_rnf["pendingOrOtherStatusCount"], 0)
        self.assertEqual(rec_rnf["notFoundCount"], 0)
        self.assertEqual(rec_rnf["unverifiedCount"], 2)
        self.assertEqual(rec_rnf["perOrder"]["ORD-RNF-1"]["state"], "QUERY_ERROR")
        self.assertEqual(rec_rnf["perOrder"]["ORD-RNF-1"]["errorCode"], "ResourceNotFoundException")
        self.assertEqual(rec_rnf["perOrder"]["ORD-RNF-2"]["state"], "QUERY_ERROR")
        self.assertEqual(rec_rnf["perOrder"]["ORD-RNF-2"]["errorCode"], "ResourceNotFoundException")

    def test_reconcile_boto_config_and_per_order_deadline_cutoff(self):
        cfg_short = load_tool.build_bounded_boto_config(0.2)
        self.assertEqual(cfg_short.connect_timeout, 0.2)
        self.assertEqual(cfg_short.read_timeout, 0.2)
        self.assertEqual(cfg_short.retries.get("total_max_attempts"), 1)
        self.assertEqual(cfg_short.retries.get("max_attempts"), 0)

        cfg_long = load_tool.build_bounded_boto_config(20.0)
        self.assertEqual(cfg_long.connect_timeout, 5.0)
        self.assertEqual(cfg_long.read_timeout, 5.0)
        self.assertEqual(cfg_long.retries.get("total_max_attempts"), 1)

        now = [50.0]

        def clock_fn() -> float:
            return now[0]

        sleeps = []

        class SlowClockDynamoTable:
            def __init__(self):
                self.queried_keys = []

            def get_item(self, **kwargs):
                oid = kwargs["Key"]["orderId"]
                self.queried_keys.append(oid)
                # First order lookup consumes the entire 0.5s budget
                now[0] += 0.6
                return {}

        slow_table = SlowClockDynamoTable()
        rec = load_tool.reconcile_orders_dynamodb(
            order_ids=["ORD-SLOW-1", "ORD-SLOW-2", "ORD-SLOW-3"],
            table_name="Orders",
            timeout_seconds=0.5,
            max_polls=4,
            dynamodb_table=slow_table,
            clock_fn=clock_fn,
            sleep_fn=sleeps.append,
        )
        # Must stop immediately after ORD-SLOW-1 exceeds deadline: no lookup for ORD-SLOW-2/3 and no backoff sleep
        self.assertEqual(slow_table.queried_keys, ["ORD-SLOW-1"])
        self.assertEqual(sleeps, [])
        self.assertEqual(rec["pollsExecuted"], 1)
        self.assertEqual(rec["perOrder"]["ORD-SLOW-1"]["attempts"], 1)
        self.assertEqual(rec["perOrder"]["ORD-SLOW-2"]["attempts"], 0)
        self.assertEqual(rec["perOrder"]["ORD-SLOW-3"]["attempts"], 0)


if __name__ == "__main__":
    unittest.main()
