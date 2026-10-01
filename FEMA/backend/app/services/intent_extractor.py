import re
from typing import Dict, Any, Optional, Tuple

class IntentExtractor:
    """
    Extracts transaction parameters (amount, currencies, countries, purpose)
    and user confirmation/cancellation intents from natural language.
    """

    FILLER_WORDS = {
        "hi", "hello", "hey", "okay", "ok", "sure", "yes", "yeah", "yep", "no", "nope",
        "fine", "alright", "then", "thn", "now", "so", "well", "actually", "please",
        "send", "transfer", "remit", "pay", "wire", "deposit", "make", "give", "help",
        "do", "proceed", "execute", "forward", "credit", "cancel", "stop", "confirm", "start",
        "want", "need", "like", "would", "it", "its", "it's", "to", "from", "for", "in", "on",
        "the", "a", "an", "my", "me", "you", "i", "we", "he", "she", "they", "them", "his", "her",
        "their", "our", "him", "someone", "anyone", "another", "something", "anything", "nothing",
        "india", "us", "usa", "america", "united", "states", "account", "bank", "sender", "recipient",
        "beneficiary", "money", "funds", "cash", "amount", "rupee", "rupees", "dollar", "dollars",
        "inr", "usd", "here", "there", "can", "could", "should", "will", "shall",
        "education", "medical", "family", "support", "service", "personal", "lottery", "gambling",
        "crypto", "bitcoin", "tuition", "studies", "living", "expenses", "fees", "instead"
    }

    @classmethod
    def is_valid_person_name(cls, name: Optional[str]) -> bool:
        """Determines if a candidate string is a plausible person's name and not a filler word, command, or amount."""
        if not name or not isinstance(name, str):
            return False
        clean = name.strip()
        if not clean or len(clean) < 2:
            return False
        # Cannot contain numbers or currency marks
        if any(ch.isdigit() or ch in "₹$€£" for ch in clean):
            return False
        tokens = [t.lower() for t in re.findall(r'\b[a-zA-Z]+\b', clean)]
        if not tokens or len(tokens) > 4:
            return False
        # If any token is in FILLER_WORDS, it's not a person name!
        if any(t in cls.FILLER_WORDS for t in tokens):
            return False
        # Every token must be at least 2 chars
        if any(len(t) < 2 for t in tokens):
            return False
        return True

    @classmethod
    def strip_conversational_fillers(cls, text: str) -> str:
        """Strips leading transitional fillers like 'thn', 'okay then', 'actually'."""
        clean = text.strip()
        clean = re.sub(
            r'^(?:okay then|ok then|fine then|alright then|well then|so then|just|actually|thn|then|okay|ok|fine|alright|now|so|well|sure|please)\s+',
            '',
            clean,
            flags=re.IGNORECASE
        ).strip()
        return clean

    @staticmethod
    def extract_confirmation(text: str) -> Optional[bool]:
        """Returns True if confirmed, False if cancelled, None if neither."""
        clean = text.lower().strip()
        tokens = re.findall(r'\b[a-z\']+\b', clean)
        if not tokens:
            return None

        # Check negative/cancellation phrases
        if any(neg in clean for neg in [
            "don't proceed", "dont proceed", "do not proceed", "no don't", "no dont",
            "cancel the transfer", "don't send", "dont send", "never mind", "nevermind", "forget it"
        ]):
            return False

        if tokens[0] in {"no", "cancel", "stop", "abort", "reject", "nevermind"}:
            return False
        if any(t in tokens for t in ["cancel", "abort"]):
            return False

        # Affirmative checks
        if any(aff in clean for aff in [
            "go ahead", "do it", "please proceed", "i confirm", "confirm transfer",
            "yes please", "send it", "okay send it", "ok send it", "yes proceed"
        ]):
            return True

        if tokens[0] in {"yes", "proceed", "confirm", "sure", "yep", "yeah", "approved"}:
            return True

        return None

    @classmethod
    def extract_amount_and_currency(cls, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extracts numerical amount and source currency from text, including Indian denominations and symbol suffixes."""
        clean = text.replace(",", "")

        # 0. Indian denominations: "10 lakh", "₹10 lakhs", "1.5 crore", "50k", "25k"
        match_lakh = re.search(r'([₹$])?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs)\b', clean, re.IGNORECASE)
        if match_lakh:
            symbol = match_lakh.group(1)
            amt = float(match_lakh.group(2)) * 100000.0
            curr = "USD" if symbol == "$" else "INR"
            return (amt, curr)

        match_crore = re.search(r'([₹$])?\s*(\d+(?:\.\d+)?)\s*(?:crore|crores|cr)\b', clean, re.IGNORECASE)
        if match_crore:
            symbol = match_crore.group(1)
            amt = float(match_crore.group(2)) * 10000000.0
            curr = "USD" if symbol == "$" else "INR"
            return (amt, curr)

        match_k = re.search(r'([₹$])?\s*(\d+(?:\.\d+)?)\s*k\b', clean, re.IGNORECASE)
        if match_k:
            symbol = match_k.group(1)
            amt = float(match_k.group(2)) * 1000.0
            curr = "USD" if symbol == "$" else "INR"
            return (amt, curr)

        # 1a. Currency symbol before amount: ₹50000 or $500 or $9,000
        match_symbol_prefix = re.search(r'([₹$€£])\s*(\d+(?:\.\d+)?)', clean)
        if match_symbol_prefix:
            symbol = match_symbol_prefix.group(1)
            amt = float(match_symbol_prefix.group(2))
            curr = "INR" if symbol == "₹" else "USD"
            return (amt, curr)

        # 1b. Currency symbol after amount: 9000$ or 50000₹ or 9000 $
        match_symbol_suffix = re.search(r'(\d+(?:\.\d+)?)\s*([₹$€£])', clean)
        if match_symbol_suffix:
            amt = float(match_symbol_suffix.group(1))
            symbol = match_symbol_suffix.group(2)
            curr = "INR" if symbol == "₹" else "USD"
            return (amt, curr)

        # 2. Amount followed by currency word: 50000 inr, 500 dollars, 9000 usd, 50000 rupees
        match_word = re.search(r'(\d+(?:\.\d+)?)\s*(inr|rupees|rupee|usd|dollars|dollar|bucks)\b', clean, re.IGNORECASE)
        if match_word:
            amt = float(match_word.group(1))
            unit = match_word.group(2).lower()
            curr = "INR" if unit in ["inr", "rupees", "rupee"] else "USD"
            return (amt, curr)

        # 3. Currency word followed by amount: "dollars 500", "rupees 50000", "usd 9000"
        match_prefix = re.search(r'\b(inr|rupees|rupee|usd|dollars|dollar)\s+(\d+(?:\.\d+)?)', clean, re.IGNORECASE)
        if match_prefix:
            unit = match_prefix.group(1).lower()
            amt = float(match_prefix.group(2))
            curr = "INR" if unit in ["inr", "rupees", "rupee"] else "USD"
            return (amt, curr)

        # 4. Standalone number if present (and not a year like 2024..2026)
        match_num = re.search(r'\b(\d+(?:\.\d+)?)\b', clean)
        if match_num:
            val = float(match_num.group(1))
            if val not in [2024, 2025, 2026]:
                curr = None
                if re.search(r'[₹]|inr|rupee|india', clean, re.IGNORECASE):
                    curr = "INR"
                elif re.search(r'[$]|usd|dollar|us|america', clean, re.IGNORECASE):
                    curr = "USD"
                return (val, curr)

        return (None, None)

    @classmethod
    def extract_updates(cls, text: str) -> Dict[str, Any]:
        """Detects explicit modifications like 'Actually make it 7000' or 'Actually send it to Rahul'."""
        updates: Dict[str, Any] = {}
        clean_lower = text.lower()
        is_update_intent = any(w in clean_lower for w in ["actually", "instead", "change to", "make it", "make the amount", "send to", "update to"])

        amt, curr = cls.extract_amount_and_currency(text)
        if amt is not None and (is_update_intent or "make it" in clean_lower or "instead" in clean_lower):
            updates["amount"] = amt
            if curr:
                updates["currency"] = curr

        m_recip = re.search(r'(?:send (?:it )?to|change recipient to|recipient is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', text, re.IGNORECASE)
        if m_recip:
            cand = m_recip.group(1).strip()
            if cls.is_valid_person_name(cand):
                updates["recipient_name"] = cand.title()

        return updates

    @classmethod
    def extract_sender(cls, text: str) -> Optional[str]:
        """Extracts declared sender name from text if specified. Immune to fillers like 'thn' or 'okay then'."""
        clean = cls.strip_conversational_fillers(text)

        # 1. Pattern: "from <Sender> to <Recipient>"
        m = re.search(r'\bfrom\s+(?:my\s+(?:india\s+|us\s+|usa\s+)?account\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+to\b', clean, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cls.is_valid_person_name(cand):
                return cand.title()

        # 2. Pattern: "<Sender> wants to send ... to <Recipient>" or "<Sender> sends ... to <Recipient>"
        m = re.search(r'^([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:wants?\s+to\s+send|sends?|transfers?)\b', clean, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cls.is_valid_person_name(cand):
                return cand.title()

        # 3. Pattern: "<Sender> to <Recipient>" at start of text
        m = re.search(r'^([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+to\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', clean, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cls.is_valid_person_name(cand):
                return cand.title()

        # 4. Pattern: "from <Sender>"
        for m in re.finditer(r'\bfrom\s+(?:my\s+(?:india\s+|us\s+|usa\s+)?account\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', clean, re.IGNORECASE):
            cand = m.group(1).strip()
            if cls.is_valid_person_name(cand):
                return cand.title()

        # 5. Pattern: "sender is <Sender>" or "sender <Sender>"
        m = re.search(r'\bsender(?:\s+is)?\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', clean, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cls.is_valid_person_name(cand):
                return cand.title()

        return None

    @classmethod
    def extract_recipient(cls, text: str) -> Optional[str]:
        """Extracts declared recipient name from text if specified. Excludes destination countries like US or India."""
        clean = cls.strip_conversational_fillers(text)

        # 1. Pattern: "to <Recipient>" (e.g. "to Meera Joshi for education", "to Abhishek")
        for m in re.finditer(r'\bto\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', clean, re.IGNORECASE):
            cand = m.group(1).strip()
            words = cand.split()
            if len(words) == 2 and words[1].lower() in ["for", "in", "from", "on", "with"]:
                cand = words[0]
            if cls.is_valid_person_name(cand):
                return cand.title()

        # 2. Pattern: "recipient is <Recipient>" or "recipient <Recipient>"
        m = re.search(r'\brecipient(?:\s+is)?\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', clean, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cls.is_valid_person_name(cand):
                return cand.title()

        return None

    @staticmethod
    def detect_adversarial_attempt(text: str) -> Optional[Dict[str, Any]]:
        """
        Detects adversarial attempts to bypass, ignore, falsify, or circumvent FEMA regulations.
        Returns a dict with violation type, category, and reason if detected, or None.
        """
        clean = text.lower()

        # 1. Explicit FEMA bypass
        if any(kw in clean for kw in [
            "ignore fema", "bypass fema", "dont worry about fema", "don't worry about fema",
            "forget fema", "skip fema", "no fema", "without fema", "disregard fema",
            "override fema", "who cares about fema"
        ]):
            return {
                "type": "EXPLICIT_FEMA_BYPASS",
                "category": "compliance_bypass",
                "reason": "User explicitly requested to ignore or bypass FEMA statutory regulations."
            }

        # 2. Refusing / skipping purpose
        if any(kw in clean for kw in [
            "don't want to tell you the purpose", "dont want to tell you the purpose",
            "won't tell you the purpose", "wont tell you the purpose",
            "skip the purpose", "skip purpose", "no purpose needed",
            "just send it without purpose", "don't ask for purpose", "dont ask for purpose",
            "none of your business", "private purpose", "why do you care about purpose"
        ]):
            return {
                "type": "REFUSE_PURPOSE",
                "category": "missing_required_declaration",
                "reason": "User refused to provide a legitimate remittance purpose required by FEMA LRS."
            }

        # 3. Refusing / skipping documentation
        if any(kw in clean for kw in [
            "don't have the required document", "dont have the required document",
            "don't have the document", "dont have the document",
            "skip documentation", "skip documents", "without documents",
            "no documentation", "process without document", "process without doc"
        ]):
            return {
                "type": "REFUSE_DOCUMENTATION",
                "category": "missing_documentation",
                "reason": "User requested processing without mandatory supporting documentation."
            }

        # 4. Falsifying purpose
        if any(kw in clean for kw in [
            "put education as the purpose even though", "put education even though",
            "fake purpose", "false purpose", "lie about purpose",
            "just put whatever purpose", "make up a purpose", "invent a purpose",
            "put a random purpose", "claim it is for education", "say it is for medical even though"
        ]):
            return {
                "type": "FALSE_PURPOSE",
                "category": "fraudulent_declaration",
                "reason": "User instructed the agent to misrepresent or fabricate a fraudulent remittance purpose."
            }

        # 5. Overriding compliance / Account owner authority
        if any(kw in clean for kw in [
            "i'm the account owner", "i am the account owner",
            "it's my money", "its my money", "don't need to follow these restrictions",
            "dont need to follow these restrictions", "i authorize you to skip",
            "you don't have to follow rules", "i order you to send"
        ]):
            return {
                "type": "OVERRIDE_AUTHORITY",
                "category": "compliance_override_attempt",
                "reason": "User claimed personal authority to override statutory banking compliance rules."
            }

        # 6. Urgency pressure to bypass checks
        if any(kw in clean for kw in [
            "extremely urgent skip", "urgent skip all", "skip all the compliance checks",
            "skip all checks and send", "hurry up and skip", "emergency bypass",
            "skip the checks now"
        ]):
            return {
                "type": "URGENCY_BYPASS",
                "category": "urgency_manipulation",
                "reason": "User used artificial urgency to pressure the agent to skip compliance validation."
            }

        # 7. Manipulating transaction details / Structuring
        if any(kw in clean for kw in [
            "change the transaction details so", "change details so that it doesn't trigger",
            "avoid the restriction", "bypass the restriction", "circumvent the limit",
            "split it so it doesn't get reported", "hide the real amount", "modify details to pass"
        ]):
            return {
                "type": "MANIPULATE_DETAILS",
                "category": "structuring_attempt",
                "reason": "User requested altering transaction details to circumvent compliance thresholds."
            }

        return None

    @staticmethod
    def extract_countries(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts source and destination countries."""
        clean = text.lower().strip()

        us_synonyms = r'(?:the\s+)?(?:us|u\.s\.|usa|u\.s\.a\.|united\s+states|america)'
        in_synonyms = r'(?:india|bharat|ind)'

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

        # Check standalone mentions if neither source nor destination set yet
        if not destination_country and not source_country:
            # Check if whole message or single word is US or India
            if re.search(rf'^{us_synonyms}$', clean) or re.search(rf'\b{us_synonyms}\b', clean):
                destination_country = "United States"
            elif re.search(rf'^{in_synonyms}$', clean) or re.search(rf'\b{in_synonyms}\b', clean):
                destination_country = "India"

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

        # Prohibited / restricted under FEMA Schedule I
        if any(kw in clean for kw in ["lottery", "sweepstakes", "sweepstake"]):
            return "Lottery purchase"
        if any(kw in clean for kw in ["gambling", "casino", "betting", "poker"]):
            return "Gambling / casino activities"
        if any(kw in clean for kw in ["crypto", "bitcoin", "ethereum", "virtual asset"]):
            return "Cryptocurrency purchase"
        if any(kw in clean for kw in ["margin trading", "forex trading", "speculation"]):
            return "Margin trading"

        # General "for <purpose>" phrase extraction
        for_match = re.search(r'\bfor\s+([A-Za-z\s]{3,35})\b', text, re.IGNORECASE)
        if for_match:
            candidate = for_match.group(1).strip()
            cand_lower = candidate.lower()
            if cand_lower not in ["the", "an", "a", "my", "him", "her", "them", "us", "india", "america"]:
                # Exclude if it looks like a person's name preceded by "for my"
                if not cand_lower.startswith("my "):
                    return candidate[0].upper() + candidate[1:]

        return None

intent_extractor = IntentExtractor()
