import json

from fintech_alerts.infrai_sms import InfraiSmsClient
from fintech_alerts.models import PaymentEvent
from fintech_alerts.payment_notifier import notify_payment


def main() -> None:
    event = PaymentEvent(
        event_id="evt-demo-1042",
        payment_id="pay-demo-1042",
        customer_phone="+15551234567",
        amount_minor=18450,
        currency="USD",
        state="declined",
        risk_score=82,
    )
    receipt = notify_payment(event, InfraiSmsClient())
    print(json.dumps(receipt.model_dump(), indent=2))


if __name__ == "__main__":
    main()

