from fintech_alerts.models import PaymentEvent
from fintech_alerts.payment_notifier import notify_payment


class RecordingSms:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.status_queries: list[str] = []

    def send(self, to: str, message: str, idempotency_key: str) -> dict[str, object]:
        self.sent.append((to, message, idempotency_key))
        return {"message_id": "sms_1042"}

    def status(self, message_id: str) -> dict[str, object]:
        self.status_queries.append(message_id)
        return {"status": "queued"}


def payment(**changes: object) -> PaymentEvent:
    values: dict[str, object] = {
        "event_id": "evt-1042",
        "payment_id": "pay-1042",
        "customer_phone": "+15551234567",
        "amount_minor": 18450,
        "currency": "USD",
        "state": "authorized",
        "risk_score": 30,
    }
    values.update(changes)
    return PaymentEvent.model_validate(values)


def test_high_risk_payment_is_sent_and_status_is_recorded() -> None:
    sms = RecordingSms()

    receipt = notify_payment(payment(risk_score=70), sms)

    assert receipt.action == "sent"
    assert receipt.reason == "risk_review"
    assert receipt.delivery_status == "queued"
    assert sms.sent[0][2] == "payment-alert:evt-1042"
    assert sms.status_queries == ["sms_1042"]


def test_routine_authorization_does_not_send() -> None:
    sms = RecordingSms()

    receipt = notify_payment(payment(risk_score=69), sms)

    assert receipt.action == "skipped"
    assert receipt.reason == "routine_payment_event"
    assert sms.sent == []
    assert sms.status_queries == []

