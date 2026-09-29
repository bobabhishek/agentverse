from typing import Dict, List, Any, Optional

def default_transaction_state() -> Dict[str, Any]:
    return {
        "source_country": None,
        "destination_country": None,
        "source_currency": None,
        "destination_currency": None,
        "amount": None,
        "purpose": None,
        "fx_rate": None,
        "converted_amount": None,
        "transfer_fee": None,
        "total_debit": None,
        "user_confirmed": False,
        "policy_evaluated": False,
        "transfer_executed": False,
        "stage": "INIT"  # INIT -> COLLECTING -> AWAITING_CONFIRMATION -> CONFIRMED -> COMPLETED / CANCELLED
    }

class ConversationStore:
    def __init__(self):
        # Maps conversation_id -> list of message dicts
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        # Maps conversation_id -> transaction state dict
        self._tx_store: Dict[str, Dict[str, Any]] = {}

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        return self._store.get(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str, extra: Optional[Dict[str, Any]] = None):
        if conversation_id not in self._store:
            self._store[conversation_id] = []
        msg = {
            "role": role,
            "content": content
        }
        if extra:
            msg.update(extra)
        self._store[conversation_id].append(msg)

    def get_transaction_state(self, conversation_id: str) -> Dict[str, Any]:
        if conversation_id not in self._tx_store:
            self._tx_store[conversation_id] = default_transaction_state()
        return self._tx_store[conversation_id]

    def update_transaction_state(self, conversation_id: str, **kwargs) -> Dict[str, Any]:
        state = self.get_transaction_state(conversation_id)
        for k, v in kwargs.items():
            if v is not None:
                state[k] = v
        return state

    def reset_transaction_state(self, conversation_id: str) -> Dict[str, Any]:
        self._tx_store[conversation_id] = default_transaction_state()
        return self._tx_store[conversation_id]

    def clear(self, conversation_id: str):
        if conversation_id in self._store:
            del self._store[conversation_id]
        if conversation_id in self._tx_store:
            del self._tx_store[conversation_id]

conversation_store = ConversationStore()

