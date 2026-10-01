import logging
from typing import List, Dict, Any, Optional
from app.services.database import db_service

logger = logging.getLogger("fema.data")

class DataLoader:
    """
    Provides data access to the persistent SQLite database test cases and customer records.
    """

    def __init__(self):
        self._db = db_service

    def get_all(self, status: str = "all") -> List[Dict[str, Any]]:
        return self._db.get_all_customers()

    def get_by_id(self, person_id: str) -> Optional[Dict[str, Any]]:
        if not person_id:
            return None
        cust = self._db.get_customer(person_id)
        if cust:
            return cust
        recip = self._db.get_recipient(person_id)
        if recip:
            d = dict(recip)
            d["customer_id"] = recip["recipient_id"]
            d["customer_name"] = recip["recipient_name"]
            d["person_id"] = recip["recipient_id"]
            d["name"] = recip["recipient_name"]
            d["source_country"] = recip.get("recipient_country", "United States")
            d["source_currency"] = "INR" if "india" in str(d["source_country"]).lower() else "USD"
            d["sender_residency"] = d["source_country"]
            return d
        return None

    def find_customer(self, query: str) -> Optional[Dict[str, Any]]:
        c = self._db.find_customer(query)
        if c:
            return c
        r = self._db.find_recipient(query)
        if r:
            d = dict(r)
            d["customer_id"] = r["recipient_id"]
            d["customer_name"] = r["recipient_name"]
            d["person_id"] = r["recipient_id"]
            d["name"] = r["recipient_name"]
            d["source_country"] = r.get("recipient_country", "United States")
            d["source_currency"] = "INR" if "india" in str(d["source_country"]).lower() else "USD"
            d["sender_residency"] = d["source_country"]
            return d
        return None

    def find_by_recipient(self, query: str) -> Optional[Dict[str, Any]]:
        # 1. Search recipients first
        r = self._db.find_recipient(query)
        if r:
            return r
        # 2. Search customers to support role reversal (customer receiving money)
        c = self._db.find_customer(query)
        if c:
            country = c.get("source_country", "India")
            curr = "INR" if "india" in country.lower() else "USD"
            return {
                "recipient_id": c["customer_id"],
                "recipient_name": c["customer_name"],
                "recipient_country": country,
                "destination_country": country,
                "destination_currency": curr,
                "inr_balance": c.get("inr_balance", 100000.0),
                "usd_balance": c.get("usd_balance", 10000.0)
            }
        return None

    def find_person(self, query: str) -> Optional[Dict[str, Any]]:
        return self._db.find_person(query)

data_loader = DataLoader()
