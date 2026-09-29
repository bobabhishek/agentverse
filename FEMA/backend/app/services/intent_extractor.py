import re
from typing import Dict, Any, Optional, Tuple

class IntentExtractor:
    """
    Extracts transaction parameters (amount, currencies, countries, purpose)
    and user confirmation/cancellation intents from natural language.
    """

    @staticmethod
    def extract_confirmation(text: str) -> Optional[bool]:
        """Returns True if confirmed, False if cancelled, None if neither."""
        tokens = re.findall(r'\b[a-z\']+\b', text.lower())
        if not tokens:
            return None

        clean = " ".join(tokens)

        # Check negative phrases first to prevent false positives
        if any(neg in clean for neg in ["don't proceed", "dont proceed", "do not proceed", "no don't", "no dont"]):
            return False

        if tokens[0] in {"no", "cancel", "stop", "abort", "reject", "nevermind"}:
            return False
        if any(t in tokens for t in ["cancel", "abort"]):
            return False

        # Affirmative checks
        if tokens[0] in {"yes", "proceed", "confirm", "sure", "yep", "yeah", "ok", "okay", "approved"}:
            return True

        if any(aff in clean for aff in ["go ahead", "do it", "please proceed", "i confirm", "confirm transfer"]):
            return True

        return None

    @staticmethod
    def extract_amount_and_currency(text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extracts numerical amount and source currency from text."""
        clean = text.replace(",", "")

        # 1. Look for currency symbol with amount: ₹50000 or $500
        match_symbol = re.search(r'([₹$€£])\s*(\d+(?:\.\d+)?)', clean)
        if match_symbol:
            symbol = match_symbol.group(1)
            amt = float(match_symbol.group(2))
            curr = "INR" if symbol == "₹" else ("USD" if symbol == "$" else "USD")
            return (amt, curr)

        # 2. Look for amount followed by currency: 50000 inr, 500 dollars, 50000 rupees
        match_word = re.search(r'(\d+(?:\.\d+)?)\s*(inr|rupees|rupee|usd|dollars|dollar|bucks)\b', clean, re.IGNORECASE)
        if match_word:
            amt = float(match_word.group(1))
            unit = match_word.group(2).lower()
            curr = "INR" if unit in ["inr", "rupees", "rupee"] else "USD"
            return (amt, curr)

        # 3. Look for currency word followed by amount: "dollars 500", "rupees 50000"
        match_prefix = re.search(r'\b(inr|rupees|rupee|usd|dollars|dollar)\s+(\d+(?:\.\d+)?)', clean, re.IGNORECASE)
        if match_prefix:
            unit = match_prefix.group(1).lower()
            amt = float(match_prefix.group(2))
            curr = "INR" if unit in ["inr", "rupees", "rupee"] else "USD"
            return (amt, curr)

        # 4. Standalone number if present (and not a year like 2026)
        match_num = re.search(r'\b(\d+(?:\.\d+)?)\b', clean)
        if match_num:
            val = float(match_num.group(1))
            if val not in [2024, 2025, 2026]:
                # Guess currency from context if present
                curr = None
                if re.search(r'\b(inr|rupee|india)\b', clean, re.IGNORECASE):
                    curr = "INR"
                elif re.search(r'\b(usd|dollar|us|america)\b', clean, re.IGNORECASE):
                    curr = "USD"
                return (val, curr)

        return (None, None)

    @staticmethod
    def extract_countries(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts source and destination countries."""
        clean = text.lower()

        us_synonyms = r'(?:the\s+)?(?:us|u\.s\.|usa|u\.s\.a\.|united\s+states|america)'
        in_synonyms = r'(?:india|in)'

        source_country = None
        destination_country = None

        # Pattern: from US to India
        if re.search(rf'from\s+(?:my\s+)?{us_synonyms}\b.*to\s+{in_synonyms}\b', clean):
            return ("United States", "India")

        # Pattern: from India to US
        if re.search(rf'from\s+(?:my\s+)?{in_synonyms}\b.*to\s+{us_synonyms}\b', clean):
            return ("India", "United States")

        # Pattern: US to India
        if re.search(rf'\b{us_synonyms}\s+to\s+{in_synonyms}\b', clean):
            return ("United States", "India")

        # Pattern: India to US
        if re.search(rf'\b{in_synonyms}\s+to\s+{us_synonyms}\b', clean):
            return ("India", "United States")

        # Check explicit destination: "to the US" or "to India"
        if re.search(rf'\bto\s+(?:my\s+[a-z]+\s+in\s+)?{us_synonyms}\b', clean):
            destination_country = "United States"
        elif re.search(rf'\bto\s+(?:my\s+[a-z]+\s+in\s+)?{in_synonyms}\b', clean):
            destination_country = "India"

        # Check explicit source: "from my US account" or "from India"
        if re.search(rf'\bfrom\s+(?:my\s+)?{us_synonyms}', clean):
            source_country = "United States"
        elif re.search(rf'\bfrom\s+(?:my\s+)?{in_synonyms}', clean):
            source_country = "India"

        return (source_country, destination_country)

    @staticmethod
    def extract_purpose(text: str) -> Optional[str]:
        """Extracts purpose from text."""
        clean = text.lower()

        # Education
        if any(kw in clean for kw in [
            "education", "tuition", "college", "university", "school",
            "study", "studies", "fees", "course", "semester"
        ]):
            return "Education expenses"

        # Medical
        if any(kw in clean for kw in [
            "medical", "hospital", "doctor", "treatment", "health",
            "surgery", "clinic", "medicine", "prescription"
        ]):
            return "Medical expenses"

        # Service / Consulting
        if any(kw in clean for kw in [
            "service", "work", "consulting", "freelance", "contractor",
            "invoice", "vendor", "software"
        ]):
            return "Service payment"

        # Emergency
        if any(kw in clean for kw in ["emergency", "urgent", "assistance"]):
            return "Emergency assistance"

        # Family support
        if any(kw in clean for kw in [
            "family support", "family", "brother", "sister", "parents",
            "mother", "father", "son", "daughter", "relative", "mom", "dad",
            "wife", "husband", "kids", "children", "household"
        ]):
            return "Family support"

        # Personal
        if any(kw in clean for kw in ["personal", "gift", "living expenses"]):
            return "Personal transfer"

        return None

intent_extractor = IntentExtractor()
