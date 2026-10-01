import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.services.database import db_service

logger = logging.getLogger("fema.routes.database")
router = APIRouter(prefix="/api/database", tags=["database"])

@router.get("/summary")
async def get_database_summary():
    """Returns persistent database statistics including table counts and last update timestamp."""
    return db_service.get_database_summary()

@router.get("/customers")
async def get_customers():
    """Returns all synthetic customers along with their current dynamic persistent account balances."""
    return db_service.get_all_customers()

@router.get("/recipients")
async def get_recipients():
    """Returns all synthetic recipients along with their current dynamic persistent account balances."""
    return db_service.get_all_recipients()

@router.get("/accounts")
async def get_accounts():
    """Returns all simulated accounts across all customers and recipients."""
    return db_service.get_all_accounts()

@router.get("/transactions")
async def get_transactions(limit: Optional[int] = Query(100, ge=1, le=500)):
    """
    Returns all completed simulated transactions, strictly sorted in descending order (newest first).
    """
    txs = db_service.get_all_transactions()
    if limit:
        return txs[:limit]
    return txs

from pydantic import BaseModel

class CreatePersonRequest(BaseModel):
    name: str
    country: str = "India"
    initial_inr: Optional[float] = 100000.0
    initial_usd: Optional[float] = 10000.0

@router.post("/create-person")
async def create_synthetic_person(req: CreatePersonRequest):
    """
    Creates a new synthetic person with persistent accounts in SQLite.
    Immediately available as sender or recipient.
    """
    if not req.name or not req.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    person = db_service.add_synthetic_person(
        name=req.name.strip(),
        residency=req.country,
        source_country=req.country,
        initial_inr=req.initial_inr or 100000.0,
        initial_usd=req.initial_usd or 10000.0
    )
    return person
