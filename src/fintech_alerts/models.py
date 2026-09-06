from enum import Enum

from pydantic import BaseModel, Field


class PaymentState(str, Enum):
    authorized = "authorized"
    declined = "declined"
    settled = "settled"


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    payment_id: str = Field(min_length=1)
    customer_phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    amount_minor: int = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    state: PaymentState
    risk_score: int = Field(ge=0, le=100)


class AlertReceipt(BaseModel):
    event_id: str
    payment_id: str
    action: str
    reason: str
    message_id: str | None = None
    delivery_status: str | None = None

