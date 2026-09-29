import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("fema.data")

class DataLoader:
    def __init__(self):
        self._test_cases: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        path = Path(settings.DATA_PATH)
        if not path.is_file():
            # Try alternate path relative to current file
            alt_path = Path(__file__).resolve().parent.parent / "data" / "fema_synthetic_100_people.json"
            if alt_path.is_file():
                path = alt_path

        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._test_cases = json.load(f)
                logger.info(f"Loaded {len(self._test_cases)} synthetic FEMA test cases from {path}")
            except Exception as e:
                logger.error(f"Failed to load synthetic dataset from {path}: {e}")
                self._test_cases = []
        else:
            logger.warning(f"Synthetic data file not found at {path}")
            self._test_cases = []

    def get_all(self, status: str = "all") -> List[Dict[str, Any]]:
        status_clean = status.lower().strip()
        if status_clean in ("policy_failure", "failures", "failure"):
            return [tc for tc in self._test_cases if len(tc.get("policy_violations", [])) > 0]
        elif status_clean in ("valid", "compliant"):
            return [tc for tc in self._test_cases if len(tc.get("policy_violations", [])) == 0]
        return self._test_cases

    def get_by_id(self, person_id: str) -> Optional[Dict[str, Any]]:
        clean_id = person_id.strip().upper()
        for tc in self._test_cases:
            if tc.get("person_id", "").upper() == clean_id:
                return tc
        return None

data_loader = DataLoader()
