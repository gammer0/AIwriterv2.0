from __future__ import annotations

from dataclasses import dataclass
import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class RelayConfig:
    base_url: str
    api_key: Optional[str] = None
    model: Optional[str] = None


class RelayHTTPError(RuntimeError):
    def __init__(self, status: int, body: str | None = None):
        super().__init__(f"Relay request failed (status={status})")
        self.status = status
        self.body = body


def _join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"


class RelayProxy:
    def __init__(self, config: RelayConfig, *, timeout_s: float = 60.0):
        if not config.base_url:
            raise ValueError("RelayConfig.base_url is required")
        self._config = config
        self._timeout_s = timeout_s

    def default_chat_path(self) -> str:
        """
        Tries to avoid common misconfiguration where base_url already includes `/v1`.
        - base_url endswith `/v1`  -> use `/chat/completions`
        - otherwise               -> use `/v1/chat/completions`
        """
        base = self._config.base_url.rstrip("/")
        if base.endswith("/v1"):
            return "/chat/completions"
        return "/v1/chat/completions"

    def request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        url = _join_url(self._config.base_url, path)
        body = None if payload is None else json.dumps(payload).encode("utf-8")

        final_headers: Dict[str, str] = {
            "Accept": "application/json",
        }
        if body is not None:
            final_headers["Content-Type"] = "application/json; charset=utf-8"
        if self._config.api_key:
            final_headers["Authorization"] = f"Bearer {self._config.api_key}"
        if headers:
            final_headers.update(headers)

        req = urllib.request.Request(url=url, method=method.upper(), data=body, headers=final_headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                status = int(resp.status)
                raw = resp.read()
                text = raw.decode("utf-8", errors="replace") if raw else "{}"
                try:
                    data = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    data = {"_raw_text": text}
                return status, data
        except urllib.error.HTTPError as e:
            raw = e.read()
            body_text = raw.decode("utf-8", errors="replace") if raw else None
            raise RelayHTTPError(int(e.code), body_text) from e

    def chat_completions(self, payload: Dict[str, Any], *, path: Optional[str] = None) -> Dict[str, Any]:
        final_path = path or self.default_chat_path()
        _, data = self.request_json("POST", final_path, payload)
        return data
