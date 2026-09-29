import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.models import ActivityEvent

logger = logging.getLogger("fema.event_logger")

class EventLogger:
    def __init__(self):
        self._events: List[ActivityEvent] = []

    def create_event(
        self,
        event_type: str,
        transaction_id: str,
        person_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityEvent:
        timestamp = datetime.now(timezone.utc).isoformat()
        evt = ActivityEvent(
            event_type=event_type,
            timestamp=timestamp,
            transaction_id=transaction_id,
            person_id=person_id,
            details=details or {}
        )
        self._events.append(evt)
        logger.info(f"EVENT [{event_type}] txn={transaction_id} person={person_id} detail={details}")
        return evt

    def get_events_for_transaction(self, transaction_id: str) -> List[ActivityEvent]:
        return [e for e in self._events if e.transaction_id == transaction_id]

event_logger = EventLogger()
