import io
import json
from email.message import Message
from urllib.error import HTTPError

from fintech_alerts.infrai_sms import InfraiSmsClient


class Reply:
    def __init__(self, status: int, body: dict[str, object], headers: Message | None = None) -> None:
        self.status = status
        self.headers = headers or Message()
        self._body = json.dumps(body).encode()

    def read(self) -> bytes:
        return self._body


def test_send_retries_with_same_identity_then_reads_status() -> None:
    requests = []

    def opener(request, timeout: int):
        requests.append(request)
        if len(requests) == 1:
            headers = Message()
            headers["Retry-After"] = "0"
            body = json.dumps({"ok": False, "data": None, "error": {"code": "RATE_LIMITED"}, "metadata": {}}).encode()
            raise HTTPError(request.full_url, 429, "busy", headers, io.BytesIO(body))
        if request.get_method() == "POST":
            return Reply(200, {"ok": True, "data": {"message_id": "sms_7"}, "error": None, "metadata": {}})
        return Reply(200, {"ok": True, "data": {"status": "queued"}, "error": None, "metadata": {}})

    client = InfraiSmsClient(api_key="test-key", base_url="https://example.test", opener=opener, sleeper=lambda _: None)
    sent = client.send("+15551234567", "Review payment pay-7", "payment-alert:evt-7")
    status = client.status(str(sent["message_id"]))

    assert [request.get_method() for request in requests] == ["POST", "POST", "GET"]
    assert requests[0].headers["Idempotency-key"] == requests[1].headers["Idempotency-key"]
    assert requests[2].full_url.endswith("/v1/sms/status/sms_7")
    assert status["status"] == "queued"

