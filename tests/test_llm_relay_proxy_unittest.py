import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

from llm.client import LLMClient
from llm.relay_proxy import RelayHTTPError


class _Handler(BaseHTTPRequestHandler):
    expected_auth: Optional[str] = None

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return

        if self.expected_auth is not None:
            got = self.headers.get("Authorization")
            if got != self.expected_auth:
                self._send_json(401, {"error": "unauthorized"})
                return

        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length).decode("utf-8")
        req = json.loads(body) if body else {}

        user_content = ""
        for m in req.get("messages", []):
            if m.get("role") == "user":
                user_content = m.get("content", "")

        self._send_json(
            200,
            {
                "id": "test",
                "object": "chat.completion",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": f"echo:{user_content}"}}],
            },
        )

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def _start_server(expected_auth: Optional[str]) -> tuple[HTTPServer, int]:
    _Handler.expected_auth = expected_auth
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = int(server.server_port)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, port


class TestLLMRelayProxy(unittest.TestCase):
    def test_llm_client_chat_roundtrip(self) -> None:
        server, port = _start_server(expected_auth="Bearer testkey")
        try:
            client = LLMClient.build(base_url=f"http://127.0.0.1:{port}", api_key="testkey", model="dummy")
            resp = client.chat("hi")
            self.assertEqual(resp.text, "echo:hi")
            self.assertIsInstance(resp.raw, dict)
        finally:
            server.shutdown()
            server.server_close()

    def test_llm_client_unauthorized_raises(self) -> None:
        server, port = _start_server(expected_auth="Bearer testkey")
        try:
            client = LLMClient.build(base_url=f"http://127.0.0.1:{port}", api_key="wrong", model="dummy")
            with self.assertRaises(RelayHTTPError):
                client.chat("hi")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
