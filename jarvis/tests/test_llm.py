import io
import json
import unittest

from jarvis import llm


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_opener(body: dict):
    def opener(request, timeout=None):
        return FakeResponse(json.dumps(body).encode("utf-8"))

    return opener


class PayloadTests(unittest.TestCase):
    def test_build_payload_shape(self):
        payload = llm.build_payload("m", "sys", [{"role": "user", "content": "hi"}])
        self.assertEqual(payload["model"], "m")
        self.assertEqual(payload["system"], "sys")
        self.assertEqual(payload["messages"][0]["content"], "hi")
        self.assertEqual(payload["max_tokens"], 1024)


class ExtractTextTests(unittest.TestCase):
    def test_joins_text_blocks_only(self):
        response = {"content": [{"type": "text", "text": "Hello "}, {"type": "tool_use"}, {"type": "text", "text": "sir"}]}
        self.assertEqual(llm.extract_text(response), "Hello sir")

    def test_rejects_unexpected_shape(self):
        with self.assertRaises(llm.LLMError):
            llm.extract_text({"error": "nope"})


class SendTests(unittest.TestCase):
    def test_returns_assistant_text(self):
        body = {"content": [{"type": "text", "text": "At your service."}]}
        text = llm.send("key", llm.build_payload("m", "s", []), opener=fake_opener(body))
        self.assertEqual(text, "At your service.")

    def test_api_error_payload_raises(self):
        body = {"type": "error", "error": {"message": "bad key"}}
        with self.assertRaisesRegex(llm.LLMError, "bad key"):
            llm.send("key", llm.build_payload("m", "s", []), opener=fake_opener(body))

    def test_transport_failure_wrapped(self):
        def broken(request, timeout=None):
            raise OSError("network down")

        with self.assertRaisesRegex(llm.LLMError, "network down"):
            llm.send("key", llm.build_payload("m", "s", []), opener=broken)

    def test_request_headers(self):
        seen = {}

        def opener(request, timeout=None):
            seen["key"] = request.get_header("X-api-key")
            seen["version"] = request.get_header("Anthropic-version")
            return FakeResponse(b'{"content": [{"type": "text", "text": "ok"}]}')

        llm.send("secret", llm.build_payload("m", "s", []), opener=opener)
        self.assertEqual(seen["key"], "secret")
        self.assertEqual(seen["version"], llm.API_VERSION)


if __name__ == "__main__":
    unittest.main()
