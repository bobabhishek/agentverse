import logging
import uuid
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.models import WireMockTransferResponse
from app.services.event_logger import event_logger

logger = logging.getLogger("fema.wiremock")

async def execute_wiremock_transfer(
    transaction_id: str,
    person_id: str,
    source_country: str,
    destination_country: str,
    amount: float,
    currency: str,
    recipient_name: str,
    purpose: str
) -> WireMockTransferResponse:
    """
    Submits simulated wire transfer to WireMock sandbox endpoint (/transfers/domestic).
    Direction-aware: handles India -> US and US -> India safely.
    Strictly simulation only; no real money or banking credentials ever move.
    """
    wiremock_base = settings.WIREMOCK_BASE_URL.strip() if settings.WIREMOCK_BASE_URL else ""
    if wiremock_base:
        # Cross-border uses /transfers/international, domestic uses /transfers/domestic
        is_cross_border = (source_country or "").lower().strip() != (destination_country or "").lower().strip()
        path = "/transfers/international" if is_cross_border else "/transfers/domestic"
        endpoint = f"{wiremock_base.rstrip('/')}{path}"
    else:
        endpoint = ""

    payload = {
        "transaction_id": transaction_id,
        "person_id": person_id,
        "source_country": source_country,
        "destination_country": destination_country,
        "amount": amount,
        "currency": currency,
        "recipient_name": recipient_name,
        "purpose": purpose,
        "environment": "SIMULATION_ONLY"
    }

    event_logger.create_event(
        event_type="WIREMOCK_REQUEST",
        transaction_id=transaction_id,
        person_id=person_id,
        details={
            "endpoint": endpoint or "MOCK_LOCAL_SANDBOX",
            "source": source_country,
            "dest": destination_country,
            "amount": f"{amount} {currency}"
        }
    )

    # If WireMock URL is configured, attempt actual HTTP call
    if endpoint:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                logger.info(f"Dispatching POST to WireMock sandbox: {endpoint}")
                resp = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if resp.status_code in (200, 201, 202):
                    try:
                        raw = resp.json()
                        import inspect
                        if inspect.isawaitable(raw):
                            raw = await raw
                    except Exception:
                        raw = {"text": resp.text}

                    payment_id = (
                        raw.get("paymentID")
                        or raw.get("payment_id")
                        or raw.get("id")
                        or f"PMT-WM-{uuid.uuid4().hex[:8].upper()}"
                    )
                    status_str = raw.get("status", "Scheduled")

                    event_logger.create_event(
                        event_type="WIREMOCK_RESPONSE",
                        transaction_id=transaction_id,
                        person_id=person_id,
                        details={"status_code": resp.status_code, "status": status_str, "payment_id": payment_id}
                    )
                    event_logger.create_event(
                        event_type="TRANSFER_SCHEDULED",
                        transaction_id=transaction_id,
                        person_id=person_id,
                        details={"payment_id": payment_id, "amount": f"{amount} {currency}"}
                    )

                    return WireMockTransferResponse(
                        success=True,
                        gateway="WireMock",
                        environment="SIMULATION",
                        status=status_str,
                        payment_id=payment_id,
                        raw_response=raw
                    )
                else:
                    err_msg = f"WireMock HTTP {resp.status_code}: {resp.text[:120]}"
                    event_logger.create_event(
                        event_type="TRANSFER_FAILED",
                        transaction_id=transaction_id,
                        person_id=person_id,
                        details={"error": err_msg}
                    )
                    return WireMockTransferResponse(
                        success=False,
                        gateway="WireMock",
                        environment="SIMULATION",
                        status="FAILED",
                        error=err_msg
                    )
        except Exception as e:
            logger.warning(f"WireMock connection failed or timed out: {e}. Falling back to sandbox response.")
            err_msg = f"WireMock sandbox unreachable: {str(e)}"
            event_logger.create_event(
                event_type="TRANSFER_FAILED",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"error": err_msg}
            )
            return WireMockTransferResponse(
                success=False,
                gateway="WireMock",
                environment="SIMULATION",
                status="FAILED",
                error=err_msg
            )

    # If no WIREMOCK_BASE_URL provided in .env, simulate WireMock standard sandbox response
    payment_id = f"PMT-SIM-{uuid.uuid4().hex[:8].upper()}"
    raw_mock = {
        "status": "Scheduled",
        "payment_id": payment_id,
        "amount": amount,
        "currency": currency,
        "route": f"{source_country} -> {destination_country}",
        "gateway": "WireMock Simulated Gateway"
    }

    event_logger.create_event(
        event_type="WIREMOCK_RESPONSE",
        transaction_id=transaction_id,
        person_id=person_id,
        details={"status": "Scheduled", "payment_id": payment_id}
    )
    event_logger.create_event(
        event_type="TRANSFER_SCHEDULED",
        transaction_id=transaction_id,
        person_id=person_id,
        details={"payment_id": payment_id, "amount": f"{amount} {currency}"}
    )

    return WireMockTransferResponse(
        success=True,
        gateway="WireMock",
        environment="SIMULATION",
        status="Scheduled",
        payment_id=payment_id,
        raw_response=raw_mock
    )
