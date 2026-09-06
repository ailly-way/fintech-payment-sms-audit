from fastapi import Depends, FastAPI, HTTPException

from .infrai_sms import InfraiError, InfraiSmsClient
from .models import AlertReceipt, PaymentEvent
from .payment_notifier import notify_payment

app = FastAPI(title="Fintech payment SMS alerts")


def sms_client() -> InfraiSmsClient:
    return InfraiSmsClient()


@app.post("/payment-events", response_model=AlertReceipt)
def accept_payment_event(
    event: PaymentEvent,
    sms: InfraiSmsClient = Depends(sms_client),
) -> AlertReceipt:
    try:
        return notify_payment(event, sms)
    except InfraiError as exc:
        client_status = exc.status if 400 <= exc.status < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": exc.detail.get("message", "request rejected")},
        ) from exc
