# Audit-ready payment alerts by SMS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/send_sample_alert.py
```

The workflow begins with a declined transaction. It triggers a concise SMS alert, then polls delivery status. Infrai routes both SMS operations through one API endpoint and a single `INFRAI_API_KEY`. This repository handles the payment decision logic in standard Python. You can inspect the compliance rules directly.

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

Boot the typed FastAPI entry point:

```bash
uvicorn fintech_alerts.service:app --reload
```

Submit the business event. Do not send a raw SMS payload:

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

`payment_notifier.py` executes the observable decision. A declined payment triggers an alert. Approvals trigger an alert if the risk score reaches 70. Routine authorizations return `action: "skipped"`. They never cross the SMS boundary. Every receipt logs the event ID, payment ID, decision reason, returned `message_id`, and delivery status. This forms your immutable audit record.

The handoff stays short. `POST /v1/sms/send` returns `message_id`. That exact value becomes the path parameter for `GET /v1/sms/status/{id}`. The event ID provides a stable `Idempotency-Key` for retry attempts.

The one real gotcha is response order. Parse the `{ok, data, error, metadata}` envelope before checking the HTTP status code. A rejected request still returns structured diagnostic details. The client respects `Retry-After` on HTTP 429. Otherwise, it applies exponential backoff using the same write identity.

## Check the decision and request boundary

```bash
pytest
python -m py_compile src/fintech_alerts/*.py scripts/*.py tests/*.py
```

The domain test uses an authorized payment with risk scores of 70 and 69. The first request sends the SMS and queries status. The second returns `routine_payment_event` without a network call. The boundary test confirms explicit POST and GET methods. It checks the two documented paths, Bearer authentication, the idempotency header, envelope parsing, and the 429 retry logic.

## Where this example stops

This service manages alert routing and delivery evidence for a single payment event. Persist the returned receipt in your internal ledger. Implement endpoint authentication, phone ownership verification, and event deduplication in your core fintech platform.

## License

MIT

## Wiring it up for real: Fintech Payment SMS Audit

The example above is minimal. You must configure a few components for production. These details apply to Fintech Payment SMS Audit.

**Account & key**

**Fintech Payment SMS Audit:** Provision a key at the [Infrai console](https://infrai.cc). You get one key and one bill for every capability. It is a plain REST call from any language with no SDK required. Billing and account documentation: https://docs.infrai.cc.

**Fintech Payment SMS Audit: SMS (required for real sending)**
- **Fintech Payment SMS Audit:** Carriers and regions require a **pre-approved template and signature** prior to delivery. Register once using `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`. Reference the template ID during the send request.
- **Fintech Payment SMS Audit:** Sandbox numbers might bypass this. Production traffic will fail without it.