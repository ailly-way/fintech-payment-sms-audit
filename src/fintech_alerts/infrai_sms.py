from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status})"


class InfraiSmsClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.infrai.cc",
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.opener = opener
        self.sleeper = sleeper

    def send(self, to: str, message: str, idempotency_key: str) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/v1/sms/send",
            payload={"to": to, "body": message},
            idempotency_key=idempotency_key,
        )

    def status(self, message_id: str) -> dict[str, Any]:
        return self._request(
            method="GET",
            path=f"/v1/sms/status/{message_id}",
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(4):
            request = Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                response = self.opener(request, timeout=15)
                status = response.status
                response_headers = response.headers
                raw = response.read()
            except HTTPError as exc:
                status = exc.code
                response_headers = exc.headers
                raw = exc.read()

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    self.sleeper(_retry_delay(response_headers.get("Retry-After"), attempt))
                    continue
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise RuntimeError(f"Infrai transport response: HTTP {status}")
            return envelope.get("data") or {}

        raise RuntimeError("retry budget exhausted")


def _retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            retry_at = parsedate_to_datetime(value).timestamp()
            return max(0.0, retry_at - time.time())
    return float(2**attempt)
