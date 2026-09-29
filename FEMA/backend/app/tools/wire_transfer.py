import logging
from typing import Dict, Any
from app.services.wiremock import execute_wiremock_transfer
from app.services.event_logger import event_logger
from app.models import WireMockTransferResponse

logger = logging.getLogger("fema.tools")

WIRE_TRANSFER_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "submit_domestic_wire",
        "description": "Submit a simulated cross-border wire transfer to the WireMock test sandbox. Strictly simulation only; no real money moves.",
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The synthetic transaction identifier, e.g. TEST-TXN-0001"
                },
                "source_country": {
                    "type": "string",
                    "description": "Originating source country (e.g. India or United States)"
                },
                "destination_country": {
                    "type": "string",
                    "description": "Destination country (e.g. United States or India)"
                },
                "amount": {
                    "type": "number",
                    "description": "Transfer amount in specified currency"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency code (e.g. USD)"
                },
                "recipient_name": {
                    "type": "string",
                    "description": "Recipient person or organization name"
                },
                "purpose": {
                    "type": "string",
                    "description": "Declared remittance purpose (e.g. Family support, Education expenses)"
                }
            },
            "required": [
                "transaction_id",
                "source_country",
                "destination_country",
                "amount",
                "currency",
                "recipient_name",
                "purpose"
            ]
        }
    }
}

async def run_submit_domestic_wire(
    transaction_id: str,
    person_id: str,
    source_country: str,
    destination_country: str,
    amount: float,
    currency: str,
    recipient_name: str,
    purpose: str
) -> WireMockTransferResponse:
    """Executes the submit_domestic_wire tool."""
    logger.info(f"Tool submit_domestic_wire called for {transaction_id} ({source_country} -> {destination_country})")
    
    event_logger.create_event(
        event_type="TRANSFER_TOOL_CALLED",
        transaction_id=transaction_id,
        person_id=person_id,
        details={
            "tool": "submit_domestic_wire",
            "direction": f"{source_country} -> {destination_country}",
            "amount": f"{amount} {currency}"
        }
    )

    return await execute_wiremock_transfer(
        transaction_id=transaction_id,
        person_id=person_id,
        source_country=source_country,
        destination_country=destination_country,
        amount=amount,
        currency=currency,
        recipient_name=recipient_name,
        purpose=purpose
    )
