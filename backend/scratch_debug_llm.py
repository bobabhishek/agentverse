import re
import unicodedata

def normalize_text(text):
    if not text:
        return ""
    normalized = unicodedata.normalize('NFD', str(text))
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').lower().strip()

def parse_user_intent_fallback(user_message: str):
    clean = user_message.strip()
    msg_lower = clean.lower()
    
    # 1. Greetings
    greetings = {"hi", "hello", "hey", "hola", "namaste", "greetings", "good morning", "good afternoon", "good evening", "help", "who are you", "what can you do", "what is this"}
    clean_stripped = msg_lower.rstrip("!?.")
    if clean_stripped in greetings or any(clean_stripped.startswith(g) for g in ["hi ", "hello ", "hey "]) or "who are you" in clean_stripped:
        return {
            "intent": "conversation",
            "reply": (
                "Hello! I am Agent 2 (India Node), an external requesting node in this cross-border architecture. "
                "I have no direct database access and route queries to Agent 1 (Europe Node). "
                "You can ask me to look up customer records, for example:\n"
                "• 'Get phone number for customer 1006' (demonstrates GDPR Data Minimization test)\n"
                "• 'Get details for Hans Russo'\n"
                "• 'give em detail of emma garcia'\n"
                "• 'Show all customers in Amsterdam'\n"
                "• 'give me detail for all 100 profiles'"
            ),
            "requested_fields": [],
            "search_parameters": {}
        }

    # 2. All 100 profiles / all customers
    if any(p in msg_lower for p in ["all 100", "100 profiles", "all profiles", "all customers", "show all", "list all"]):
        return {
            "intent": "list_customer_names",
            "requested_fields": ["id", "name", "country", "city"],
            "search_parameters": {"all": True}
        }

    # 3. Customer ID lookup
    id_match = re.search(r'\b(?:customer\s*|id\s*)?(?:syn-cust-)?(\d{4})\b', msg_lower)
    if id_match and ("customer" in msg_lower or "syn-cust" in msg_lower or "id" in msg_lower or "phone" in msg_lower or "gps" in msg_lower):
        cust_id = f"SYN-CUST-{id_match.group(1)}"
        if "phone" in msg_lower and not any(kw in msg_lower for kw in ["all", "address", "gps", "order"]):
            req_fields = ["id", "phone"]
        elif "gps" in msg_lower:
            req_fields = ["id", "gps"]
        else:
            req_fields = ["id", "name", "country", "city", "phone", "address", "order_status"]
        return {
            "intent": "get_customer_details",
            "requested_fields": req_fields,
            "search_parameters": {"id": cust_id}
        }

    # 4. City lookup
    cities = ["amsterdam", "paris", "berlin", "london", "rome", "copenhagen", "madrid"]
    for city in cities:
        if city in msg_lower:
            return {
                "intent": "list_customer_names",
                "requested_fields": ["id", "name", "city", "country"],
                "search_parameters": {"city": city.capitalize()}
            }

    # 5. Country lookup
    countries = ["germany", "netherlands", "france", "uk", "italy", "spain", "denmark"]
    for country in countries:
        if country in msg_lower:
            return {
                "intent": "list_customer_names",
                "requested_fields": ["name", "country", "city"],
                "search_parameters": {"country": country.capitalize() if country != "uk" else "UK"}
            }

    # 6. Order status lookup
    statuses = ["cancelled", "delivered", "shipped", "processing"]
    for status in statuses:
        if status in msg_lower:
            return {
                "intent": "list_customer_names",
                "requested_fields": ["id", "name", "order_status", "city"],
                "search_parameters": {"order_status": status.capitalize()}
            }

    # 7. Name lookup (e.g. "Get details for Hans Russo", "give em detail of emma garcia", "Emma Davies")
    name_patterns = [
        r'(?:details?|info|profile|detail)\s+(?:for|of|on|about)\s+([a-zA-Z\u00C0-\u017F\s]+)',
        r'(?:find|search|lookup|get|show)\s+(?:customer\s+)?([a-zA-Z\u00C0-\u017F\s]+)',
        r'(?:any|name)\s+([a-zA-Z\u00C0-\u017F\s]+)'
    ]
    for pat in name_patterns:
        m = re.search(pat, clean, re.IGNORECASE)
        if m:
            target_name = m.group(1).strip()
            # Clean trailing words
            for stop in ["phone", "number", "address", "gps", "please"]:
                target_name = re.sub(rf'\b{stop}\b', '', target_name, flags=re.IGNORECASE).strip()
            if target_name and len(target_name) > 2:
                # If specifically phone was asked
                if "phone" in msg_lower and not any(kw in msg_lower for kw in ["all", "address", "gps", "order"]):
                    req_fields = ["id", "phone", "name"]
                else:
                    req_fields = ["id", "name", "country", "city", "phone", "address", "order_status"]
                return {
                    "intent": "get_customer_details" if " " in target_name else "list_customer_names",
                    "requested_fields": req_fields,
                    "search_parameters": {"name": target_name}
                }

    return None

test_queries = [
    "hi",
    "Get details for Hans Russo",
    "give me detail for all 100 profiles",
    "give em detail of emma garcia",
    "give detail any emma or name emma",
    "Get phone number for customer 1006",
    "Show all customers in Amsterdam",
    "Show cancelled orders",
    "What is the GPS of id SYN-CUST-1003?"
]

for q in test_queries:
    res = parse_user_intent_fallback(q)
    print(f"QUERY: {q}")
    print(f"  Parsed: {res}")
