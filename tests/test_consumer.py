"""Focused unit tests for SV1 Quan SQS Consumer Lambda PoC.

Standard-library unittest only. Deterministic local tests without AWS,
credentials, or third-party dependencies.
"""

import importlib.util
import json
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parent.parent / "src" / "consumer" / "lambda_function.py"


def _load_consumer():
    """Load consumer module without mutating sys.path or sys.modules."""
    spec = importlib.util.spec_from_file_location("consumer_lambda_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_consumer()
lambda_handler = mod.lambda_handler
ConsumerError = mod.ConsumerError


class TestConsumerPoC(unittest.TestCase):
    """Single test case covering all required consumer PoC behavior and security controls."""

    def _make_event(self, *records):
        return {"Records": list(records)}

    def _make_record(self, body, message_id="msg-001"):
        return {
            "messageId": message_id,
            "body": json.dumps(body) if not isinstance(body, str) else body,
        }

    def _base_payload(self, **overrides):
        payload = {"orderId": "ORD-001", "items": [{"sku": "SKU-001", "quantity": 1}]}
        payload.update(overrides)
        return payload

    def _run_and_parse_logs(self, event, expect_error_code=None):
        """Execute handler, assert exact exception if expected, and parse every LogRecord as JSON."""
        with self.assertLogs("consumer", level="INFO") as cm:
            if expect_error_code:
                with self.assertRaises(ConsumerError) as ctx:
                    lambda_handler(event)
                self.assertEqual(str(ctx.exception), expect_error_code)
                self.assertEqual(ctx.exception.error_code, expect_error_code)
                if expect_error_code == "INVALID_JSON":
                    self.assertIsNone(ctx.exception.__cause__)
                    self.assertTrue(ctx.exception.__suppress_context__)
                res = None
            else:
                res = lambda_handler(event)

        # Parse every log record strictly; any non-JSON log fails immediately
        parsed_logs = [json.loads(r.getMessage()) for r in cm.records]
        return res, parsed_logs, cm.output

    def test_success_single_and_multiple_records(self):
        # 1. Single valid record
        record1 = self._make_record(
            self._base_payload(orderId="ORD-W1-Q-003", items=[{"sku": "S1", "quantity": 2}]),
            "msg-101",
        )
        res1, logs1, _ = self._run_and_parse_logs(self._make_event(record1))
        self.assertEqual(res1, {"statusCode": 200, "status": "POC_VALIDATED", "processedCount": 1})
        self.assertEqual(len(logs1), 1)
        self.assertEqual(
            logs1[0],
            {"level": "INFO", "status": "POC_VALIDATED", "messageId": "msg-101", "orderId": "ORD-W1-Q-003", "itemCount": 1},
        )

        # 2. Multiple valid records
        r1 = self._make_record(self._base_payload(orderId="ORD-1"), "m-1")
        r2 = self._make_record(
            self._base_payload(orderId="ORD-2", items=[{"sku": "A", "quantity": 1}, {"sku": "B", "quantity": 3}]),
            "m-2",
        )
        res2, logs2, _ = self._run_and_parse_logs(self._make_event(r1, r2))
        self.assertEqual(res2["processedCount"], 2)
        self.assertEqual([l["orderId"] for l in logs2], ["ORD-1", "ORD-2"])
        self.assertEqual([l["itemCount"] for l in logs2], [1, 2])

        # 3. Extra fields permitted by contract
        res3, logs3, _ = self._run_and_parse_logs(
            self._make_event(self._make_record(self._base_payload(clientTimestamp="2026-10-11", note="safe")))
        )
        self.assertEqual(res3["processedCount"], 1)
        self.assertEqual(logs3[0]["orderId"], "ORD-001")

    def test_malformed_event_table(self):
        cases = [
            ("none", None),
            ("string", "not_a_dict"),
            ("int", 123),
            ("missing_records", {}),
            ("records_none", {"Records": None}),
            ("records_str", {"Records": "invalid"}),
            ("records_empty", {"Records": []}),
        ]
        for desc, event in cases:
            with self.subTest(case=desc):
                _, logs, _ = self._run_and_parse_logs(event, expect_error_code="MALFORMED_EVENT")
                self.assertEqual(logs[0], {"level": "ERROR", "errorCode": "MALFORMED_EVENT", "messageId": "UNKNOWN"})

    def test_malformed_record_and_body_table(self):
        cases = [
            ("record_none", None, "UNKNOWN"),
            ("record_str", "not_dict", "UNKNOWN"),
            ("missing_body", {"messageId": "m-no-body"}, "UNKNOWN"),
            ("body_none", {"messageId": "m-none", "body": None}, "m-none"),
            ("body_int", {"messageId": "m-int", "body": 123}, "m-int"),
            ("body_dict", {"messageId": "m-dict", "body": {"a": 1}}, "m-dict"),
            ("body_list", {"messageId": "m-list", "body": ["a"]}, "m-list"),
        ]
        for desc, record, expected_msg_id in cases:
            with self.subTest(case=desc):
                _, logs, _ = self._run_and_parse_logs({"Records": [record]}, expect_error_code="MALFORMED_RECORD")
                self.assertEqual(logs[0], {"level": "ERROR", "errorCode": "MALFORMED_RECORD", "messageId": expected_msg_id})

    def test_invalid_json_table(self):
        cases = [
            ("empty", ""),
            ("unclosed", "{"),
            ("single_quotes", "{'orderId': 'O1'}"),
            ("unquoted_keys", "{orderId: 1}"),
            ("plain_text", "not json text"),
        ]
        for desc, body_str in cases:
            with self.subTest(case=desc):
                event = self._make_event({"messageId": f"msg-json-{desc}", "body": body_str})
                _, logs, _ = self._run_and_parse_logs(event, expect_error_code="INVALID_JSON")
                self.assertEqual(logs[0], {"level": "ERROR", "errorCode": "INVALID_JSON", "messageId": f"msg-json-{desc}"})

    def test_invalid_schema_table(self):
        cases = [
            # Root type not dict
            ("root_int", "12345"),
            ("root_list", '[{"orderId": "O1"}]'),
            ("root_str", '"string"'),
            ("root_bool", "true"),
            ("root_null", "null"),
            # orderId invalid
            ("order_id_missing", {"items": [{"sku": "A", "quantity": 1}]}),
            ("order_id_none", self._base_payload(orderId=None)),
            ("order_id_empty", self._base_payload(orderId="")),
            ("order_id_whitespace", self._base_payload(orderId="   ")),
            ("order_id_bool_true", self._base_payload(orderId=True)),
            ("order_id_bool_false", self._base_payload(orderId=False)),
            ("order_id_int", self._base_payload(orderId=123)),
            ("order_id_list", self._base_payload(orderId=["ORD-1"])),
            ("order_id_dict", self._base_payload(orderId={"id": "ORD-1"})),
            # items invalid
            ("items_missing", {"orderId": "ORD-1"}),
            ("items_none", self._base_payload(items=None)),
            ("items_empty", self._base_payload(items=[])),
            ("items_str", self._base_payload(items="SKU-1")),
            ("items_int", self._base_payload(items=123)),
            ("items_dict_not_list", self._base_payload(items={"sku": "A", "quantity": 1})),
            ("item_none", self._base_payload(items=[None])),
            ("item_str", self._base_payload(items=["str"])),
            # sku invalid
            ("sku_missing", self._base_payload(items=[{"quantity": 1}])),
            ("sku_none", self._base_payload(items=[{"sku": None, "quantity": 1}])),
            ("sku_empty", self._base_payload(items=[{"sku": "", "quantity": 1}])),
            ("sku_whitespace", self._base_payload(items=[{"sku": "   ", "quantity": 1}])),
            ("sku_bool_true", self._base_payload(items=[{"sku": True, "quantity": 1}])),
            ("sku_bool_false", self._base_payload(items=[{"sku": False, "quantity": 1}])),
            ("sku_int", self._base_payload(items=[{"sku": 999, "quantity": 1}])),
            ("sku_list", self._base_payload(items=[{"sku": ["A"], "quantity": 1}])),
            # quantity invalid: 0, negative, both bool, integral/fractional float, string, None
            ("qty_missing", self._base_payload(items=[{"sku": "A"}])),
            ("qty_zero", self._base_payload(items=[{"sku": "A", "quantity": 0}])),
            ("qty_negative", self._base_payload(items=[{"sku": "A", "quantity": -1}])),
            ("qty_bool_true", self._base_payload(items=[{"sku": "A", "quantity": True}])),
            ("qty_bool_false", self._base_payload(items=[{"sku": "A", "quantity": False}])),
            ("qty_float_integral", self._base_payload(items=[{"sku": "A", "quantity": 1.0}])),
            ("qty_float_fractional", self._base_payload(items=[{"sku": "A", "quantity": 1.5}])),
            ("qty_str_digit", self._base_payload(items=[{"sku": "A", "quantity": "1"}])),
            ("qty_str_text", self._base_payload(items=[{"sku": "A", "quantity": "one"}])),
            ("qty_none", self._base_payload(items=[{"sku": "A", "quantity": None}])),
        ]
        for desc, payload in cases:
            with self.subTest(case=desc):
                event = self._make_event(self._make_record(payload, message_id=f"msg-schema-{desc}"))
                _, logs, _ = self._run_and_parse_logs(event, expect_error_code="INVALID_SCHEMA")
                self.assertEqual(logs[0]["errorCode"], "INVALID_SCHEMA")
                self.assertEqual(logs[0]["messageId"], f"msg-schema-{desc}")

    def test_full_batch_propagation_on_error(self):
        r1 = self._make_record(self._base_payload(orderId="ORD-VALID"), "m-val")
        r2 = self._make_record(self._base_payload(items=[{"sku": "A", "quantity": 0}]), "m-inv")
        event = self._make_event(r1, r2)
        _, logs, _ = self._run_and_parse_logs(event, expect_error_code="INVALID_SCHEMA")
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["status"], "POC_VALIDATED")
        self.assertEqual(logs[0]["orderId"], "ORD-VALID")
        self.assertEqual(logs[1]["errorCode"], "INVALID_SCHEMA")
        self.assertEqual(logs[1]["messageId"], "m-inv")

    def test_sentinel_privacy_in_success_and_failure_logs(self):
        sentinel_sku = "CONFIDENTIAL_SKU_SENTINEL_888"
        sentinel_secret = "SUPER_SECRET_PAYLOAD_TOKEN_777"

        # 1. Success path
        event_ok = self._make_event(
            self._make_record(
                self._base_payload(items=[{"sku": sentinel_sku, "quantity": 1}], secretKey=sentinel_secret),
                "m-ok",
            )
        )
        _, logs_ok, raw_ok = self._run_and_parse_logs(event_ok)
        self.assertEqual(set(logs_ok[0].keys()), {"level", "status", "messageId", "orderId", "itemCount"})
        combined_ok = " ".join(raw_ok)
        self.assertNotIn(sentinel_sku, combined_ok)
        self.assertNotIn(sentinel_secret, combined_ok)

        # 2. Failure path with invalid schema
        event_fail_schema = self._make_event(
            self._make_record({"orderId": "O1", "secret": sentinel_secret, "items": []}, "m-fail-schema")
        )
        _, logs_fs, raw_fs = self._run_and_parse_logs(event_fail_schema, expect_error_code="INVALID_SCHEMA")
        self.assertEqual(set(logs_fs[0].keys()), {"level", "errorCode", "messageId"})
        self.assertNotIn(sentinel_secret, " ".join(raw_fs))

        # 3. Failure path with malformed JSON (verify no decode context leak)
        bad_json = f'{{"malformed": "{sentinel_secret}", unclosed'
        event_fail_json = self._make_event({"messageId": "m-fail-json", "body": bad_json})
        _, logs_fj, raw_fj = self._run_and_parse_logs(event_fail_json, expect_error_code="INVALID_JSON")
        self.assertEqual(set(logs_fj[0].keys()), {"level", "errorCode", "messageId"})
        self.assertNotIn(sentinel_secret, " ".join(raw_fj))

    def test_safe_identifier_sanitization_and_injection(self):
        dirty_chars = "\r\nINJECT\t\x00\x1b-SAFE"
        dirty_order_id = f"ORD{dirty_chars}"
        dirty_msg_id = f"MSG{dirty_chars}"

        # 1. Success path: safe printable values without raw control characters
        event_ok = self._make_event(self._make_record(self._base_payload(orderId=dirty_order_id), dirty_msg_id))
        _, logs_ok, raw_ok = self._run_and_parse_logs(event_ok)
        for ch in ("\r", "\n", "\t", "\x00", "\x1b"):
            self.assertNotIn(ch, logs_ok[0]["orderId"])
            self.assertNotIn(ch, logs_ok[0]["messageId"])
        self.assertEqual(len(raw_ok), 1)
        self.assertNotIn("\r", raw_ok[0])
        self.assertNotIn("\n", raw_ok[0])

        # 2. Error path: safe printable messageId without raw control characters
        event_err = self._make_event({"messageId": dirty_msg_id, "body": "invalid-json"})
        _, logs_err, raw_err = self._run_and_parse_logs(event_err, expect_error_code="INVALID_JSON")
        for ch in ("\r", "\n", "\t", "\x00", "\x1b"):
            self.assertNotIn(ch, logs_err[0]["messageId"])
        self.assertEqual(len(raw_err), 1)
        self.assertNotIn("\r", raw_err[0])
        self.assertNotIn("\n", raw_err[0])

        # 3. Length bounding for long ASCII identifiers
        long_id = "A" * 300
        event_long = self._make_event(self._make_record(self._base_payload(orderId=long_id), long_id))
        _, logs_long, _ = self._run_and_parse_logs(event_long)
        self.assertEqual(len(logs_long[0]["orderId"]), 128)
        self.assertEqual(len(logs_long[0]["messageId"]), 128)


if __name__ == "__main__":
    unittest.main()
