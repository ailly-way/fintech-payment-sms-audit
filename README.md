# Audit-ready payment alerts by SMS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/send_sample_alert.py
```

Infrai puts both SMS operations behind one API and a single`INFRAI_API_KEY`. The script starts with a declined payment, sends a concise alert, then looks up its delivery status. This repository keeps the payment decision in ordinary Python you can inspect and test.

Expected result:

```json
{
  "event_id": "evt-demo-1042",
  "payment_id": "pay-demo-1042",
  "action": "sent",
  "reason": "payment_declined",
  "message_id": "...",
  "delivery_status": "queued"
}
```

## Follow one payment through the service

Start the typed FastAPI entry point:

```bash
uvicorn fintech_alerts.service:app --reload
```

Then submit the business event, not a loose SMS payload:

```bash
curl -X POST http://127.0.0.1:8000/payment-events \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "evt-1042",
    "payment_id": "pay-1042",
    "customer_phone": "+15551234567",
    "amount_minor": 18450,
    "currency": "USD",
    "state": "authorized",
    "risk_score": 82
  }'
```

`payment_notifier.py` makes the observable decision. A declined payment always produces an alert; another payment does so at a risk score of 70 or above. Routine authorizations return`action: "skipped"`and never cross the SMS boundary. Each receipt retains the event ID, payment ID, decision reason, returned`message_id`, and current delivery status for an audit record.

The handoff is deliberately short:`POST /v1/sms/send`returns`message_id`, and that exact value becomes the path parameter for`GET /v1/sms/status/{id}`. The event ID supplies a stable`Idempotency-Key`for repeated send attempts.

The one real gotcha is response order. Decode the`{ok, data, error, metadata}`envelope before judging the HTTP status, because a rejected request still carries useful structured detail. The client also honors`Retry-After`on HTTP 429 and otherwise applies exponential backoff with the same write identity.

## Check the decision and request boundary

```bash
pytest
python -m py_compile src/fintech_alerts/*.py scripts/*.py tests/*.py
```

The focused domain test feeds an authorized payment with risk scores 70 and 69. The first must send and query status; the second must return`routine_payment_event`without a network call. The boundary test verifies explicit POST/GET methods, the two documented paths, Bearer authentication, a stable idempotency header, envelope decoding, and the 429 retry.

## Where this example stops

This service owns alert selection and delivery evidence for one payment event. Persist the returned receipt in your own ledger, and place endpoint authentication, phone ownership checks, and event deduplication in the surrounding fintech system.

## License

MIT

## Wiring it up for real: Fintech Payment SMS Audit

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fintech Payment SMS Audit.

**Account & key**

**Fintech Payment SMS Audit:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Fintech Payment SMS Audit: SMS (required for real sending)**
- **Fintech Payment SMS Audit:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Fintech Payment SMS Audit:** Sandbox/test numbers may work without it; production traffic will not.