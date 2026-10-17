"""Offline smoke/unit tests for the Producer: mock SQS; never call AWS."""

import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

if "boto3" not in sys.modules:
    sys.modules["boto3"] = MagicMock()

PATH = Path(__file__).resolve().parent.parent / "src" / "producer" / "lambda_function.py"


class ProducerValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sqs = MagicMock()
        cls.test_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        with patch.dict(os.environ, {"QUEUE_URL": cls.test_queue_url}), patch("boto3.client", return_value=cls.sqs):
            spec = importlib.util.spec_from_file_location("producer_validation_candidate", PATH)
            cls.mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.mod)

    def setUp(self):
        self.sqs.reset_mock()
        self.sqs.send_message.side_effect = None

    def invoke(self, payload):
        event = {"body": json.dumps(payload)} if not isinstance(payload, str) else {"body": payload}
        result = self.mod.lambda_handler(event, None)
        return result["statusCode"], json.loads(result["body"])

    def assertBad(self, payload):
        status, response = self.invoke(payload)
        self.assertEqual(status, 400, response)
        self.sqs.send_message.assert_not_called()

    def test_valid(self):
        status, data = self.invoke({"customerId": "CUS01", "productId": "P01", "quantity": 2})
        self.assertEqual(status, 202)
        self.assertEqual(data["order"]["quantity"], 2)
        self.assertEqual(data["order"]["status"], "PENDING")
        self.sqs.send_message.assert_called_once()
        body = json.loads(self.sqs.send_message.call_args.kwargs["MessageBody"])
        self.assertEqual(body["orderId"], data["order"]["orderId"])

    def test_missing_customerId(self):
        self.assertBad({"productId": "P01", "quantity": 2})

    def test_missing_productId(self):
        self.assertBad({"customerId": "CUS01", "quantity": 2})

    def test_empty_ids(self):
        for field in ("customerId", "productId"):
            obj = {"customerId": "CUS01", "productId": "P01", "quantity": 2}
            obj[field] = "  "
            with self.subTest(field=field):
                self.assertBad(obj)

    def test_missing_quantity(self):
        self.assertBad({"customerId": "CUS01", "productId": "P01"})

    def test_zero_quantity(self):
        self.assertBad({"customerId": "CUS01", "productId": "P01", "quantity": 0})

    def test_negative_quantity(self):
        self.assertBad({"customerId": "CUS01", "productId": "P01", "quantity": -1})

    def test_fractional_quantity(self):
        self.assertBad({"customerId": "CUS01", "productId": "P01", "quantity": 1.5})

    def test_boolean_quantity(self):
        self.assertBad({"customerId": "CUS01", "productId": "P01", "quantity": True})
        self.assertBad({"customerId": "CUS01", "productId": "P01", "quantity": False})

    def test_string_quantity(self):
        self.assertBad({"customerId": "CUS01", "productId": "P01", "quantity": "2"})

    def test_malformed_json(self):
        self.assertBad("{not-json")

    def test_non_object_json(self):
        self.assertBad("[]")
        self.assertBad('"string-body"')

    def test_missing_body(self):
        response = self.mod.lambda_handler({}, None)
        self.assertEqual(response["statusCode"], 400)
        self.sqs.send_message.assert_not_called()

    def test_empty_body(self):
        for empty_val in ("", "   "):
            with self.subTest(val=empty_val):
                response = self.mod.lambda_handler({"body": empty_val}, None)
                self.assertEqual(response["statusCode"], 400)
                self.sqs.send_message.assert_not_called()

    def test_non_dict_event(self):
        for bad_event in (None, "string", [1, 2, 3]):
            with self.subTest(event=bad_event):
                response = self.mod.lambda_handler(bad_event, None)
                self.assertEqual(response["statusCode"], 400)
                self.sqs.send_message.assert_not_called()

    def test_sqs_failure(self):
        self.sqs.send_message.side_effect = RuntimeError("fake SQS failure")
        status, payload = self.invoke({"customerId": "CUS01", "productId": "P01", "quantity": 2})
        self.assertEqual(status, 500)
        self.assertEqual(payload["message"], "Internal server error")

    def test_flat_schema_and_queue_url(self):
        status, data = self.invoke({"customerId": "CUST-999", "productId": "PROD-888", "quantity": 5})
        self.assertEqual(status, 202)
        call_kwargs = self.sqs.send_message.call_args.kwargs
        self.assertEqual(call_kwargs["QueueUrl"], self.test_queue_url)
        sent_body = json.loads(call_kwargs["MessageBody"])
        expected_keys = {"orderId", "customerId", "productId", "quantity", "status", "createdAt"}
        self.assertEqual(set(sent_body.keys()), expected_keys)
        self.assertEqual(sent_body["customerId"], "CUST-999")
        self.assertEqual(sent_body["productId"], "PROD-888")
        self.assertEqual(sent_body["quantity"], 5)
        self.assertEqual(sent_body["status"], "PENDING")

    def test_no_sensitive_payload_or_credential_logging(self):
        secret_customer = "PRIVATE_STUDENT_ID_9999"
        secret_product = "SECRET_PRODUCT_TOKEN_1111"
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            status, data = self.invoke({"customerId": secret_customer, "productId": secret_product, "quantity": 1})
            self.assertEqual(status, 202)

        output = captured.getvalue()
        self.assertIn("ORDER_SENT_TO_SQS", output)
        self.assertNotIn(secret_customer, output)
        self.assertNotIn(secret_product, output)
        parsed_log = json.loads(output.split("ORDER_SENT_TO_SQS")[1].strip())
        self.assertEqual(set(parsed_log.keys()), {"orderId", "status"})


if __name__ == "__main__":
    unittest.main()
