from .infrai_sms import InfraiSmsClient
from .models import AlertReceipt, PaymentEvent, PaymentState


def alert_reason(event: PaymentEvent) -> str | None:
    if event.state is PaymentState.declined:
        return "payment_declined"
    if event.risk_score >= 70:
        return "risk_review"
    return None


def notify_payment(event: PaymentEvent, sms: InfraiSmsClient) -> AlertReceipt:
    reason = alert_reason(event)
    if reason is None:
        return AlertReceipt(
            event_id=event.event_id,
            payment_id=event.payment_id,
            action="skipped",
            reason="routine_payment_event",
        )

    amount = f"{event.amount_minor / 100:.2f} {event.currency}"
    if reason == "payment_declined":
        message = f"Payment {event.payment_id} for {amount} was declined. Review it in your account."
    else:
        message = f"Payment {event.payment_id} for {amount} needs a security review."

    sent = sms.send(event.customer_phone, message, f"payment-alert:{event.event_id}")
    message_id = str(sent["message_id"])
    delivery = sms.status(message_id)
    return AlertReceipt(
        event_id=event.event_id,
        payment_id=event.payment_id,
        action="sent",
        reason=reason,
        message_id=message_id,
        delivery_status=str(delivery["status"]),
    )
