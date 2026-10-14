"""Focused unit tests for SV1 Quan SQS Consumer Lambda Week 2 DynamoDB & Idempotency.

Standard unittest with mocked boto3/botocore SDK. Deterministic local tests
without AWS credentials or live cloud resources.
"""

from decimal import Decimal
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import boto3
from botocore.exceptions import ClientError

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
ERR_MALFORMED_EVENT = mod.ERR_MALFORMED_EVENT
ERR_MALFORMED_RECORD = mod.ERR_MALFORMED_RECORD
ERR_INVALID_JSON = mod.ERR_INVALID_JSON
ERR_INVALID_SCHEMA = mod.ERR_INVALID_SCHEMA
ERR_INTERNAL_ERROR = mod.ERR_INTERNAL_ERROR
ERR_CONFIG_ERROR = mod.ERR_CONFIG_ERROR
ERR_ORDER_CONFLICT = mod.ERR_ORDER_CONFLICT
ERR_ITEM_NOT_FOUND = mod.ERR_ITEM_NOT_FOUND


class MockDynamoDBTable:
    """Deterministic in-memory mock DynamoDB Table for local testing."""

    def __init__(self, initial_items=None):
        self.items = dict(initial_items or {})
        self.put_calls = []
        self.get_calls = []
        self.put_exception = None
        self.get_exception = None

    def put_item(self, Item, ConditionExpression=None):
        self.put_calls.append({"Item": Item, "ConditionExpression": ConditionExpression})
        if self.put_exception:
            raise self.put_exception
        order_id = Item.get("orderId")
        if ConditionExpression == "attribute_not_exists(orderId)":
            if order_id in self.items:
                raise ClientError(
                    {"Error": {"Code": "ConditionalCheckFailedException"}},
                    "PutItem",
                )
        self.items[order_id] = dict(Item)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def get_item(self, Key, ConsistentRead=False):
        self.get_calls.append({"Key": Key, "ConsistentRead": ConsistentRead})
        if self.get_exception:
            raise self.get_exception
        order_id = Key.get("orderId")
        item = self.items.get(order_id)
        if item is not None:
            return {"Item": dict(item)}
        return {}


class TestConsumerWeek2(unittest.TestCase):
    """Comprehensive test case covering Week 2 consumer DynamoDB integration and idempotency."""

    def setUp(self):
        self._orig_table_name = os.environ.get("TABLE_NAME")
        os.environ["TABLE_NAME"] = "Orders"

    def tearDown(self):
        if self._orig_table_name is not None:
            os.environ["TABLE_NAME"] = self._orig_table_name
        else:
            os.environ.pop("TABLE_NAME", None)

    def _make_event(self, *records):
        return {"Records": list(records)}

    def _make_record(self, body, message_id="msg-001"):
        return {
            "messageId": message_id,
            "body": json.dumps(body) if not isinstance(body, str) else body,
        }

    def _base_payload(self, **overrides):
        payload = {
            "orderId": "ORD-W2-001",
            "customerId": "CUS001",
            "productId": "P001",
            "quantity": 2,
            "status": "PENDING",
            "createdAt": "2026-10-14T00:00:00+00:00",
        }
        payload.update(overrides)
        return payload

    def _run_and_parse_logs(
        self,
        event,
        table=None,
        expect_error_code=None,
        expect_exception_type=None,
        bypass_table_setup=False,
    ):
        """Execute handler, assert exact exception if expected, and parse every LogRecord as JSON."""
        if table is None and not bypass_table_setup:
            table = MockDynamoDBTable()

        mock_resource = MagicMock()
        if table is not None:
            mock_resource.Table.return_value = table

        with patch.object(mod.boto3, "resource", return_value=mock_resource):
            with self.assertLogs("consumer", level="INFO") as cm:
                if expect_error_code:
                    with self.assertRaises(ConsumerError) as ctx:
                        lambda_handler(event)
                    self.assertEqual(str(ctx.exception), expect_error_code)
                    self.assertEqual(ctx.exception.error_code, expect_error_code)
                    if expect_error_code == ERR_INVALID_JSON:
                        self.assertIsNone(ctx.exception.__cause__)
                        self.assertTrue(ctx.exception.__suppress_context__)
                    res = None
                elif expect_exception_type:
                    with self.assertRaises(expect_exception_type):
                        lambda_handler(event)
                    res = None
                else:
                    res = lambda_handler(event)

        parsed_logs = [json.loads(r.getMessage()) for r in cm.records]
        return res, parsed_logs, cm.output

    def test_normal_production_entry_and_resource_wiring(self):
        """Assert normal handler entry invokes boto3.resource('dynamodb') and resource.Table(TABLE_NAME)."""
        fake_table = MockDynamoDBTable()
        record = self._make_record(
            self._base_payload(orderId="ORD-PROD-001"),
            "msg-prod-001",
        )
        event = self._make_event(record)

        with patch.object(mod.boto3, "resource") as mock_resource_fn:
            mock_resource = MagicMock()
            mock_resource.Table.return_value = fake_table
            mock_resource_fn.return_value = mock_resource

            res = lambda_handler(event)

            # Assert normal production wiring using TABLE_NAME from env
            mock_resource_fn.assert_called_once_with("dynamodb")
            mock_resource.Table.assert_called_once_with("Orders")

            # Assert conditional put was performed and final status is PROCESSED
            self.assertEqual(len(fake_table.put_calls), 1)
            self.assertEqual(
                fake_table.put_calls[0]["ConditionExpression"],
                "attribute_not_exists(orderId)",
            )
            self.assertEqual(fake_table.put_calls[0]["Item"]["status"], "PROCESSED")
            self.assertEqual(fake_table.items["ORD-PROD-001"]["status"], "PROCESSED")
            self.assertEqual(res, {"statusCode": 200, "status": "PROCESSED", "processedCount": 1})

    def test_success_single_and_multiple_records(self):
        # 1. Single valid record
        table1 = MockDynamoDBTable()
        record1 = self._make_record(
            self._base_payload(orderId="ORD-W2-001"),
            "msg-101",
        )
        res1, logs1, _ = self._run_and_parse_logs(self._make_event(record1), table=table1)
        self.assertEqual(res1, {"statusCode": 200, "status": "PROCESSED", "processedCount": 1})
        self.assertEqual(len(logs1), 1)
        self.assertEqual(
            logs1[0],
            {"level": "INFO", "status": "PROCESSED", "messageId": "msg-101", "orderId": "ORD-W2-001"},
        )
        self.assertEqual(len(table1.put_calls), 1)
        self.assertEqual(table1.put_calls[0]["ConditionExpression"], "attribute_not_exists(orderId)")
        self.assertEqual(table1.items["ORD-W2-001"]["status"], "PROCESSED")
        self.assertEqual(table1.items["ORD-W2-001"]["quantity"], 2)

        # 2. Multiple valid records in single batch
        table2 = MockDynamoDBTable()
        r1 = self._make_record(self._base_payload(orderId="ORD-1"), "m-1")
        r2 = self._make_record(
            self._base_payload(orderId="ORD-2", customerId="CUS002", productId="P002", quantity=5),
            "m-2",
        )
        res2, logs2, _ = self._run_and_parse_logs(self._make_event(r1, r2), table=table2)
        self.assertEqual(res2["processedCount"], 2)
        self.assertEqual([l["orderId"] for l in logs2], ["ORD-1", "ORD-2"])
        self.assertEqual([l["status"] for l in logs2], ["PROCESSED", "PROCESSED"])
        self.assertEqual(len(table2.put_calls), 2)
        self.assertEqual(table2.items["ORD-1"]["quantity"], 2)
        self.assertEqual(table2.items["ORD-2"]["quantity"], 5)

        # 3. Extra fields permitted by contract
        table3 = MockDynamoDBTable()
        res3, logs3, _ = self._run_and_parse_logs(
            self._make_event(self._make_record(self._base_payload(clientTimestamp="2026-10-14", note="safe-extra"))),
            table=table3,
        )
        self.assertEqual(res3["processedCount"], 1)
        self.assertEqual(logs3[0]["orderId"], "ORD-W2-001")
        self.assertEqual(table3.items["ORD-W2-001"]["note"], "safe-extra")

    def test_identical_duplicate_and_final_status_difference(self):
        # Existing item in DB has final status PROCESSED
        initial_item = {
            "orderId": "ORD-W2-001",
            "customerId": "CUS001",
            "productId": "P001",
            "quantity": 2,
            "status": "PROCESSED",
            "createdAt": "2026-10-14T00:00:00+00:00",
        }
        table = MockDynamoDBTable(initial_items={"ORD-W2-001": initial_item})

        # Incoming retry message has status PENDING (final status difference)
        retry_msg = self._make_record(
            self._base_payload(
                orderId="ORD-W2-001",
                customerId="CUS001",
                productId="P001",
                quantity=2,
                status="PENDING",
                createdAt="2026-10-14T00:00:00+00:00",
            ),
            "msg-retry",
        )

        res, logs, _ = self._run_and_parse_logs(self._make_event(retry_msg), table=table)
        self.assertEqual(res, {"statusCode": 200, "status": "PROCESSED", "processedCount": 1})
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0],
            {"level": "INFO", "status": "PROCESSED", "messageId": "msg-retry", "orderId": "ORD-W2-001"},
        )
        # PutItem attempted once (hit condition failure), GetItem called with ConsistentRead=True
        self.assertEqual(len(table.put_calls), 1)
        self.assertEqual(len(table.get_calls), 1)
        self.assertEqual(table.get_calls[0]["Key"], {"orderId": "ORD-W2-001"})
        self.assertTrue(table.get_calls[0]["ConsistentRead"])
        # Original item was NOT overwritten
        self.assertEqual(table.items["ORD-W2-001"]["status"], "PROCESSED")

        # Decimal quantity compatibility in existing DB item
        initial_item_dec = dict(initial_item)
        initial_item_dec["quantity"] = Decimal(2)
        table_dec = MockDynamoDBTable(initial_items={"ORD-W2-001": initial_item_dec})
        res_dec, logs_dec, _ = self._run_and_parse_logs(self._make_event(retry_msg), table=table_dec)
        self.assertEqual(res_dec["processedCount"], 1)
        self.assertEqual(logs_dec[0]["status"], "PROCESSED")

    def test_conflict_on_each_stable_business_field(self):
        conflicts = [
            ("customerId", "DIFFERENT_CUSTOMER"),
            ("productId", "DIFFERENT_PRODUCT"),
            ("quantity", 99),
            ("createdAt", "2026-10-15T00:00:00+00:00"),
        ]
        for field_name, conflicting_val in conflicts:
            with self.subTest(conflicting_field=field_name):
                original_item = {
                    "orderId": "ORD-CONF-001",
                    "customerId": "CUS001",
                    "productId": "P001",
                    "quantity": 2,
                    "status": "PROCESSED",
                    "createdAt": "2026-10-14T00:00:00+00:00",
                }
                table = MockDynamoDBTable(initial_items={"ORD-CONF-001": original_item})

                incoming_payload = self._base_payload(
                    orderId="ORD-CONF-001",
                    **{field_name: conflicting_val},
                )
                event = self._make_event(self._make_record(incoming_payload, f"msg-conf-{field_name}"))

                _, logs, _ = self._run_and_parse_logs(
                    event,
                    table=table,
                    expect_error_code=ERR_ORDER_CONFLICT,
                )
                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0]["errorCode"], ERR_ORDER_CONFLICT)
                self.assertEqual(logs[0]["messageId"], f"msg-conf-{field_name}")
                # Original item was preserved without overwriting
                self.assertEqual(table.items["ORD-CONF-001"][field_name], original_item[field_name])
                # PutItem was NOT called a second time
                self.assertEqual(len(table.put_calls), 1)

    def test_temporary_write_failures(self):
        # 1. Non-ConditionalCheckFailed ClientError (e.g. ProvisionedThroughputExceededException)
        table1 = MockDynamoDBTable()
        table1.put_exception = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException"}},
            "PutItem",
        )
        event1 = self._make_event(self._make_record(self._base_payload(), "m-write-fail-1"))
        _, logs1, _ = self._run_and_parse_logs(event1, table=table1, expect_exception_type=ClientError)
        self.assertEqual(len(logs1), 1)
        self.assertEqual(logs1[0]["errorCode"], ERR_INTERNAL_ERROR)

        # 2. Generic write exception propagates
        table2 = MockDynamoDBTable()
        table2.put_exception = RuntimeError("Connection timeout to DynamoDB")
        event2 = self._make_event(self._make_record(self._base_payload(), "m-write-fail-2"))
        _, logs2, _ = self._run_and_parse_logs(event2, table=table2, expect_exception_type=RuntimeError)
        self.assertEqual(len(logs2), 1)
        self.assertEqual(logs2[0]["errorCode"], ERR_INTERNAL_ERROR)

    def test_temporary_read_failures(self):
        # 1. ClientError during consistent read on conflict
        initial_item = self._base_payload(status="PROCESSED")
        table1 = MockDynamoDBTable(initial_items={"ORD-W2-001": initial_item})
        table1.get_exception = ClientError(
            {"Error": {"Code": "InternalServerError"}},
            "GetItem",
        )
        event1 = self._make_event(self._make_record(self._base_payload(), "m-read-fail-1"))
        _, logs1, _ = self._run_and_parse_logs(event1, table=table1, expect_exception_type=ClientError)
        self.assertEqual(len(logs1), 1)
        self.assertEqual(logs1[0]["errorCode"], ERR_INTERNAL_ERROR)

        # 2. Generic read exception propagates
        table2 = MockDynamoDBTable(initial_items={"ORD-W2-001": initial_item})
        table2.get_exception = RuntimeError("DynamoDB service unavailable")
        event2 = self._make_event(self._make_record(self._base_payload(), "m-read-fail-2"))
        _, logs2, _ = self._run_and_parse_logs(event2, table=table2, expect_exception_type=RuntimeError)
        self.assertEqual(len(logs2), 1)
        self.assertEqual(logs2[0]["errorCode"], ERR_INTERNAL_ERROR)

    def test_missing_existing_item_after_condition_failure(self):
        # Condition failed on PutItem, but GetItem returns no item
        table = MockDynamoDBTable()
        table.put_exception = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException"}},
            "PutItem",
        )
        event = self._make_event(self._make_record(self._base_payload(), "m-missing-item"))
        _, logs, _ = self._run_and_parse_logs(event, table=table, expect_error_code=ERR_ITEM_NOT_FOUND)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["errorCode"], ERR_ITEM_NOT_FOUND)

    def test_missing_table_name(self):
        for val in [None, "", "   "]:
            with self.subTest(table_name=val):
                if val is None:
                    os.environ.pop("TABLE_NAME", None)
                else:
                    os.environ["TABLE_NAME"] = val
                event = self._make_event(self._make_record(self._base_payload(), "m-no-tbl"))
                _, logs, _ = self._run_and_parse_logs(
                    event,
                    table=None,
                    expect_error_code=ERR_CONFIG_ERROR,
                    bypass_table_setup=True,
                )
                self.assertEqual(logs[0]["errorCode"], ERR_CONFIG_ERROR)

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
                _, logs, _ = self._run_and_parse_logs(event, expect_error_code=ERR_MALFORMED_EVENT)
                self.assertEqual(logs[0], {"level": "ERROR", "errorCode": ERR_MALFORMED_EVENT, "messageId": "UNKNOWN"})

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
                _, logs, _ = self._run_and_parse_logs(
                    {"Records": [record]},
                    expect_error_code=ERR_MALFORMED_RECORD,
                )
                self.assertEqual(logs[0], {"level": "ERROR", "errorCode": ERR_MALFORMED_RECORD, "messageId": expected_msg_id})

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
                _, logs, _ = self._run_and_parse_logs(event, expect_error_code=ERR_INVALID_JSON)
                self.assertEqual(logs[0], {"level": "ERROR", "errorCode": ERR_INVALID_JSON, "messageId": f"msg-json-{desc}"})

    def test_invalid_schema_table(self):
        cases = [
            # Root type not dict
            ("root_int", "12345"),
            ("root_list", '[{"orderId": "O1"}]'),
            ("root_str", '"string"'),
            ("root_bool", "true"),
            ("root_null", "null"),
            # orderId invalid
            ("order_id_missing", {"customerId": "C1", "productId": "P1", "quantity": 1, "status": "PENDING", "createdAt": "2026-10-14T00:00:00+00:00"}),
            ("order_id_none", self._base_payload(orderId=None)),
            ("order_id_empty", self._base_payload(orderId="")),
            ("order_id_whitespace", self._base_payload(orderId="   ")),
            ("order_id_bool_true", self._base_payload(orderId=True)),
            ("order_id_bool_false", self._base_payload(orderId=False)),
            ("order_id_int", self._base_payload(orderId=123)),
            ("order_id_list", self._base_payload(orderId=["ORD-1"])),
            ("order_id_dict", self._base_payload(orderId={"id": "ORD-1"})),
            # customerId invalid
            ("customer_id_missing", {"orderId": "O1", "productId": "P1", "quantity": 1, "status": "PENDING", "createdAt": "2026-10-14T00:00:00+00:00"}),
            ("customer_id_none", self._base_payload(customerId=None)),
            ("customer_id_empty", self._base_payload(customerId="")),
            ("customer_id_whitespace", self._base_payload(customerId="   ")),
            ("customer_id_bool_true", self._base_payload(customerId=True)),
            ("customer_id_int", self._base_payload(customerId=123)),
            # productId invalid
            ("product_id_missing", {"orderId": "O1", "customerId": "C1", "quantity": 1, "status": "PENDING", "createdAt": "2026-10-14T00:00:00+00:00"}),
            ("product_id_none", self._base_payload(productId=None)),
            ("product_id_empty", self._base_payload(productId="")),
            ("product_id_whitespace", self._base_payload(productId="   ")),
            ("product_id_bool_true", self._base_payload(productId=True)),
            ("product_id_int", self._base_payload(productId=123)),
            # status invalid
            ("status_missing", {"orderId": "O1", "customerId": "C1", "productId": "P1", "quantity": 1, "createdAt": "2026-10-14T00:00:00+00:00"}),
            ("status_none", self._base_payload(status=None)),
            ("status_empty", self._base_payload(status="")),
            ("status_whitespace", self._base_payload(status="   ")),
            ("status_bool_true", self._base_payload(status=True)),
            ("status_int", self._base_payload(status=123)),
            # createdAt invalid
            ("created_at_missing", {"orderId": "O1", "customerId": "C1", "productId": "P1", "quantity": 1, "status": "PENDING"}),
            ("created_at_none", self._base_payload(createdAt=None)),
            ("created_at_empty", self._base_payload(createdAt="")),
            ("created_at_whitespace", self._base_payload(createdAt="   ")),
            ("created_at_bool_true", self._base_payload(createdAt=True)),
            ("created_at_int", self._base_payload(createdAt=123)),
            # quantity invalid: 0, negative, both bool, integral/fractional float, string, None
            ("qty_missing", {"orderId": "O1", "customerId": "C1", "productId": "P1", "status": "PENDING", "createdAt": "2026-10-14T00:00:00+00:00"}),
            ("qty_zero", self._base_payload(quantity=0)),
            ("qty_negative", self._base_payload(quantity=-1)),
            ("qty_bool_true", self._base_payload(quantity=True)),
            ("qty_bool_false", self._base_payload(quantity=False)),
            ("qty_float_integral", self._base_payload(quantity=1.0)),
            ("qty_float_fractional", self._base_payload(quantity=1.5)),
            ("qty_str_digit", self._base_payload(quantity="1")),
            ("qty_str_text", self._base_payload(quantity="two")),
            ("qty_none", self._base_payload(quantity=None)),
        ]
        for desc, payload in cases:
            with self.subTest(case=desc):
                event = self._make_event(self._make_record(payload, message_id=f"msg-schema-{desc}"))
                _, logs, _ = self._run_and_parse_logs(event, expect_error_code=ERR_INVALID_SCHEMA)
                self.assertEqual(logs[0]["errorCode"], ERR_INVALID_SCHEMA)
                self.assertEqual(logs[0]["messageId"], f"msg-schema-{desc}")

    def test_full_batch_propagation_and_replay(self):
        table = MockDynamoDBTable()
        r1 = self._make_record(self._base_payload(orderId="ORD-VALID-1"), "m-val-1")
        r2 = self._make_record(self._base_payload(orderId="ORD-INVALID-2", quantity=0), "m-inv-2")
        event = self._make_event(r1, r2)

        # 1. Batch execution fails on Record 2; Record 1 was already committed to DynamoDB
        _, logs, _ = self._run_and_parse_logs(event, table=table, expect_error_code=ERR_INVALID_SCHEMA)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["status"], "PROCESSED")
        self.assertEqual(logs[0]["orderId"], "ORD-VALID-1")
        self.assertEqual(logs[1]["errorCode"], ERR_INVALID_SCHEMA)
        self.assertEqual(logs[1]["messageId"], "m-inv-2")
        self.assertIn("ORD-VALID-1", table.items)
        self.assertEqual(table.items["ORD-VALID-1"]["status"], "PROCESSED")

        # 2. Replay batch with corrected Record 2: Record 1 deduplicates as identical duplicate
        r2_fixed = self._make_record(self._base_payload(orderId="ORD-VALID-2", quantity=3), "m-val-2")
        replay_event = self._make_event(r1, r2_fixed)
        res_replay, logs_replay, _ = self._run_and_parse_logs(replay_event, table=table)
        self.assertEqual(res_replay["processedCount"], 2)
        self.assertEqual(len(logs_replay), 2)
        self.assertEqual(logs_replay[0]["status"], "PROCESSED")
        self.assertEqual(logs_replay[1]["status"], "PROCESSED")
        self.assertIn("ORD-VALID-2", table.items)

    def test_sentinel_privacy_in_success_and_failure_logs(self):
        sentinel_customer = "CONFIDENTIAL_CUST_SENTINEL_888"
        sentinel_product = "CONFIDENTIAL_PROD_SENTINEL_999"
        sentinel_secret = "SUPER_SECRET_PAYLOAD_TOKEN_777"

        # 1. Success path: no customerId, productId, or secretKey in log records
        event_ok = self._make_event(
            self._make_record(
                self._base_payload(
                    customerId=sentinel_customer,
                    productId=sentinel_product,
                    secretKey=sentinel_secret,
                ),
                "m-ok",
            )
        )
        _, logs_ok, raw_ok = self._run_and_parse_logs(event_ok)
        self.assertEqual(set(logs_ok[0].keys()), {"level", "status", "messageId", "orderId"})
        combined_ok = " ".join(raw_ok)
        self.assertNotIn(sentinel_customer, combined_ok)
        self.assertNotIn(sentinel_product, combined_ok)
        self.assertNotIn(sentinel_secret, combined_ok)

        # 2. Failure path with invalid schema: no secret tokens in log records
        event_fail_schema = self._make_event(
            self._make_record(
                {"orderId": "O1", "secret": sentinel_secret, "quantity": 0},
                "m-fail-schema",
            )
        )
        _, logs_fs, raw_fs = self._run_and_parse_logs(event_fail_schema, expect_error_code=ERR_INVALID_SCHEMA)
        self.assertEqual(set(logs_fs[0].keys()), {"level", "errorCode", "messageId"})
        self.assertNotIn(sentinel_secret, " ".join(raw_fs))

        # 3. Failure path with malformed JSON: no decode context leak
        bad_json = f'{{"malformed": "{sentinel_secret}", unclosed'
        event_fail_json = self._make_event({"messageId": "m-fail-json", "body": bad_json})
        _, logs_fj, raw_fj = self._run_and_parse_logs(event_fail_json, expect_error_code=ERR_INVALID_JSON)
        self.assertEqual(set(logs_fj[0].keys()), {"level", "errorCode", "messageId"})
        self.assertNotIn(sentinel_secret, " ".join(raw_fj))

        # 4. Failure path with conflict: differing customerId does not leak in log
        table_conf = MockDynamoDBTable(
            initial_items={"ORD-W2-001": self._base_payload(customerId="ORIGINAL_CUST", status="PROCESSED")}
        )
        event_conf = self._make_event(
            self._make_record(
                self._base_payload(customerId=sentinel_customer),
                "m-conf-sentinel",
            )
        )
        _, logs_conf, raw_conf = self._run_and_parse_logs(
            event_conf, table=table_conf, expect_error_code=ERR_ORDER_CONFLICT
        )
        self.assertEqual(set(logs_conf[0].keys()), {"level", "errorCode", "messageId"})
        self.assertNotIn(sentinel_customer, " ".join(raw_conf))
        self.assertNotIn("ORIGINAL_CUST", " ".join(raw_conf))

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
        _, logs_err, raw_err = self._run_and_parse_logs(event_err, expect_error_code=ERR_INVALID_JSON)
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
