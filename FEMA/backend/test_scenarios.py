import urllib.request
import json
import sys
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== Starting End-to-End Verification of FEMA Dynamic Banking Simulation ===")

# 1. Check initial DB state
db_summary = get_json("/api/database/summary")
print(f"Total customers in DB: {db_summary['total_customers']}")
print(f"Total recipients in DB: {db_summary['total_recipients']}")
print(f"Total transactions in DB: {db_summary['total_transactions']}")

def get_person_balance(name_or_id):
    accounts = get_json("/api/database/accounts")
    clean = name_or_id.strip().lower()
    inr = next((a["balance"] for a in accounts if (a["owner_id"].lower() == clean or (a.get("owner_name") and a["owner_name"].lower() == clean)) and a["currency"] == "INR"), 0.0)
    usd = next((a["balance"] for a in accounts if (a["owner_id"].lower() == clean or (a.get("owner_name") and a["owner_name"].lower() == clean)) and a["currency"] == "USD"), 0.0)
    return {"INR": inr, "USD": usd}

# ----------------------------------------------------
# TEST 1: INDIA DOMESTIC (Bhavya Patel -> Rahul Kumar)
# ----------------------------------------------------
print("\n--- TEST 1: INDIA DOMESTIC (Bhavya Patel -> Rahul Kumar, ₹10,000 INR) ---")
bhavya_inr_before = get_person_balance("CUST-0076")["INR"] # Bhavya Patel
rahul_inr_before = get_person_balance("Rahul Kumar")["INR"] # Rahul Kumar
print(f"Before: Bhavya INR = ₹{bhavya_inr_before:,.2f}, Rahul INR = ₹{rahul_inr_before:,.2f}")

conv1_id = f"test-conv-india-domestic-{int(datetime.now().timestamp()) if 'datetime' in globals() else 101}"
# Step 1: Initiate
r1 = post_json("/api/chat", {
    "message": "Send ₹10,000 to Rahul Kumar for family support",
    "person_id": "CUST-0076",
    "conversation_id": conv1_id,
    "source_country": "India",
    "destination_country": "India"
})
print("Agent reply 1:", r1["message"][:120], "...")

# Step 2: Confirm
r2 = post_json("/api/chat", {
    "message": "Yes, proceed with transfer",
    "person_id": "CUST-0076",
    "conversation_id": conv1_id,
    "source_country": "India",
    "destination_country": "India"
})
print("Agent reply 2:", r2["message"][:120], "...")
print("Transfer executed:", r2.get("transfer", {}).get("success"))

# Check balances after
bhavya_inr_after = get_person_balance("CUST-0076")["INR"]
rahul_inr_after = get_person_balance("Rahul Kumar")["INR"]
print(f"After: Bhavya INR = ₹{bhavya_inr_after:,.2f} (debited ₹{bhavya_inr_before - bhavya_inr_after:,.2f}), Rahul INR = ₹{rahul_inr_after:,.2f} (credited ₹{rahul_inr_after - rahul_inr_before:,.2f})")
assert bhavya_inr_after < bhavya_inr_before, "Bhavya was not debited!"
assert rahul_inr_after > rahul_inr_before, "Rahul was not credited!"
print("✓ Test 1 Passed!")

# ----------------------------------------------------
# TEST 2: INDIA TO USA (Bhavya Patel -> Meera Joshi, ₹10,000 INR -> USD)
# ----------------------------------------------------
print("\n--- TEST 2: INDIA TO USA (Bhavya Patel -> Meera Joshi, ₹10,000 INR -> USD) ---")
bhavya_inr_before2 = get_person_balance("CUST-0076")["INR"]
meera_usd_before = get_person_balance("Meera Joshi")["USD"]
print(f"Before: Bhavya INR = ₹{bhavya_inr_before2:,.2f}, Meera USD = ${meera_usd_before:,.2f}")

conv2_id = f"test-conv-india-usa-{int(datetime.now().timestamp()) if 'datetime' in globals() else 202}"
r1 = post_json("/api/chat", {
    "message": "Send ₹10,000 to Meera Joshi for education expenses",
    "person_id": "CUST-0076",
    "conversation_id": conv2_id,
    "source_country": "India",
    "destination_country": "United States"
})
r2 = post_json("/api/chat", {
    "message": "Yes, please execute the transfer",
    "person_id": "CUST-0076",
    "conversation_id": conv2_id,
    "source_country": "India",
    "destination_country": "United States"
})
print("Agent reply:", r2["message"][:120], "...")
bhavya_inr_after2 = get_person_balance("CUST-0076")["INR"]
meera_usd_after = get_person_balance("Meera Joshi")["USD"]
print(f"After: Bhavya INR = ₹{bhavya_inr_after2:,.2f} (debited ₹{bhavya_inr_before2 - bhavya_inr_after2:,.2f}), Meera USD = ${meera_usd_after:,.2f} (credited ${meera_usd_after - meera_usd_before:,.2f})")
assert bhavya_inr_after2 < bhavya_inr_before2, "Bhavya was not debited!"
assert meera_usd_after > meera_usd_before, "Meera was not credited USD!"
print("✓ Test 2 Passed!")

# ----------------------------------------------------
# TEST 3: USA DOMESTIC (USA Account -> Meera Joshi, $500 USD)
# ----------------------------------------------------
print("\n--- TEST 3: USA DOMESTIC (USA Account -> USA Recipient, $500 USD) ---")
custs = get_json("/api/database/customers")
us_cust = next((c for c in custs if c["source_country"] == "United States"), custs[0])
us_cust_id = us_cust["customer_id"]
print(f"US Customer selected: {us_cust['customer_name']} ({us_cust_id})")

p_sender_before3 = get_person_balance(us_cust_id)["USD"]
p_meera_before3 = get_person_balance("Meera Joshi")["USD"]
print(f"Before: {us_cust['customer_name']} USD = ${p_sender_before3:,.2f}, Meera USD = ${p_meera_before3:,.2f}")

conv3_id = f"test-conv-usa-domestic-{int(datetime.now().timestamp()) if 'datetime' in globals() else 303}"
r1 = post_json("/api/chat", {
    "message": "Send $500 to Meera Joshi for living expenses",
    "person_id": us_cust_id,
    "conversation_id": conv3_id,
    "source_country": "United States",
    "destination_country": "United States"
})
r2 = post_json("/api/chat", {
    "message": "Yes, confirm transaction",
    "person_id": us_cust_id,
    "conversation_id": conv3_id,
    "source_country": "United States",
    "destination_country": "United States"
})
p_sender_after3 = get_person_balance(us_cust_id)["USD"]
p_meera_after3 = get_person_balance("Meera Joshi")["USD"]
print(f"After: {us_cust['customer_name']} USD = ${p_sender_after3:,.2f} (debited ${p_sender_before3 - p_sender_after3:,.2f}), Meera USD = ${p_meera_after3:,.2f} (credited ${p_meera_after3 - p_meera_before3:,.2f})")
assert p_sender_after3 < p_sender_before3, "US sender was not debited!"
assert p_meera_after3 > p_meera_before3, "US recipient was not credited!"
print("✓ Test 3 Passed!")

# ----------------------------------------------------
# TEST 4: USA TO INDIA (USA Account -> Bhavya Patel, $500 USD -> INR)
# ----------------------------------------------------
print("\n--- TEST 4: USA TO INDIA (USA Account -> Bhavya Patel, $500 USD -> INR) ---")
p_sender_before4 = get_person_balance(us_cust_id)["USD"]
bhavya_inr_before4 = get_person_balance("CUST-0076")["INR"]
print(f"Before: {us_cust['customer_name']} USD = ${p_sender_before4:,.2f}, Bhavya INR = ₹{bhavya_inr_before4:,.2f}")

conv4_id = f"test-conv-usa-india-{int(datetime.now().timestamp()) if 'datetime' in globals() else 404}"
r1 = post_json("/api/chat", {
    "message": "Send $500 to Bhavya Patel for consultancy services",
    "person_id": us_cust_id,
    "conversation_id": conv4_id,
    "source_country": "United States",
    "destination_country": "India"
})
r2 = post_json("/api/chat", {
    "message": "Yes, please proceed",
    "person_id": us_cust_id,
    "conversation_id": conv4_id,
    "source_country": "United States",
    "destination_country": "India"
})
p_sender_after4 = get_person_balance(us_cust_id)["USD"]
bhavya_inr_after4 = get_person_balance("CUST-0076")["INR"]
print(f"After: {us_cust['customer_name']} USD = ${p_sender_after4:,.2f} (debited ${p_sender_before4 - p_sender_after4:,.2f}), Bhavya INR = ₹{bhavya_inr_after4:,.2f} (credited ₹{bhavya_inr_after4 - bhavya_inr_before4:,.2f})")
assert p_sender_after4 < p_sender_before4, "US sender was not debited!"
assert bhavya_inr_after4 > bhavya_inr_before4, "Bhavya was not credited INR!"
print("✓ Test 4 Passed!")

# ----------------------------------------------------
# TEST 5: ROLE REVERSAL (Rahul Kumar -> Bhavya Patel)
# ----------------------------------------------------
print("\n--- TEST 5: ROLE REVERSAL (Rahul Kumar sends money to Bhavya Patel) ---")
rahul_inr_before5 = get_person_balance("Rahul Kumar")["INR"]
bhavya_inr_before5 = get_person_balance("CUST-0076")["INR"]
print(f"Before: Rahul INR = ₹{rahul_inr_before5:,.2f}, Bhavya INR = ₹{bhavya_inr_before5:,.2f}")

conv5_id = f"test-conv-role-reversal-{int(datetime.now().timestamp()) if 'datetime' in globals() else 505}"
# Rahul Kumar acts as the sender
r1 = post_json("/api/chat", {
    "message": "Send ₹5,000 to Bhavya Patel for rent payment",
    "person_id": "REC-0008",
    "conversation_id": conv5_id,
    "source_country": "India",
    "destination_country": "India"
})
r2 = post_json("/api/chat", {
    "message": "Yes, proceed with payment",
    "person_id": "REC-0008",
    "conversation_id": conv5_id,
    "source_country": "India",
    "destination_country": "India"
})
rahul_inr_after5 = get_person_balance("Rahul Kumar")["INR"]
bhavya_inr_after5 = get_person_balance("CUST-0076")["INR"]
print(f"After: Rahul INR = ₹{rahul_inr_after5:,.2f} (debited ₹{rahul_inr_before5 - rahul_inr_after5:,.2f}), Bhavya INR = ₹{bhavya_inr_after5:,.2f} (credited ₹{bhavya_inr_after5 - bhavya_inr_before5:,.2f})")
assert rahul_inr_after5 < rahul_inr_before5, "Rahul was not debited as sender!"
assert bhavya_inr_after5 > bhavya_inr_before5, "Bhavya was not credited as recipient!"
print("✓ Test 5 Passed!")

# ----------------------------------------------------
# Check Latest Transactions in DB (must be ordered newest first)
# ----------------------------------------------------
print("\n--- Checking Latest Transactions Ordering in SQLite ---")
txns = get_json("/api/database/transactions")
print(f"Found {len(txns)} transactions in database:")
for i, t in enumerate(txns[:5]):
    amt_s = t.get('amount_sent', t.get('amount', 0))
    amt_r = t.get('recipient_amount', t.get('converted_amount', 0))
    ts = t.get('timestamp', t.get('created_at', ''))
    print(f"  #{i+1}: {t['sender_name']} ({t['sender_id']}) -> {t['recipient_name']} ({t['recipient_id']}) | {amt_s} {t['source_currency']} -> {amt_r} {t['destination_currency']} | {ts}")

assert txns[0]["sender_name"] == "Rahul Kumar", f"Expected latest sender to be Rahul Kumar, got {txns[0]['sender_name']}"
assert txns[0]["recipient_name"] == "Bhavya Patel", f"Expected latest recipient to be Bhavya Patel, got {txns[0]['recipient_name']}"
print("✓ Latest transaction ordering verified!")

print("\n=======================================================")
print("ALL 5 TESTS + DATABASE PERSISTENCE VERIFIED SUCCESSFULLY!")
print("=======================================================")
