import logging
from fastapi import APIRouter, HTTPException, Response
from app.services.ledger_service import ledger_service

logger = logging.getLogger("fema.routes.ledger")
router = APIRouter()

@router.get("/api/accounts/balance")
async def get_account_balances():
    """Returns current simulated sender balances and list of completed conversation IDs."""
    return ledger_service.get_summary_balances()

@router.get("/api/audit-trail/{conversation_id}")
async def get_audit_trail_json(conversation_id: str):
    """Returns the completed transaction audit trail record for a specific conversation."""
    record = ledger_service.get_audit_trail(conversation_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No completed transaction found for conversation '{conversation_id}'")
    return record

@router.get("/api/audit-trail/{conversation_id}/download")
async def download_audit_trail_pdf(conversation_id: str):
    """Downloads a certified PDF audit trail document for the transaction completed in this conversation."""
    record = ledger_service.get_audit_trail(conversation_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No completed transaction found for conversation '{conversation_id}'")

    pdf_bytes = ledger_service.generate_audit_trail_pdf(conversation_id)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate audit trail PDF")

    txn_id = record.get("transaction_id", conversation_id)
    filename = f"audit-trail-{txn_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
