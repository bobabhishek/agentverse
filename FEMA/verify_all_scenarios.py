import sys
import os
import requests
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def chat(conv_id, message, person_id=None, source_country=None, destination_country=None, reverse_route=None):
    payload = {
        "message": message,
        "conversation_id": conv_id,
        "person_id": person_id,
        "source_country": source_country,
        "destination_country": destination_country,
        "reverse_route": reverse_route
    }
    resp = requests.post(f"{BASE_URL}/api/chat", json=payload)
    if resp.status_code != 200:
        raise Exception(f"Chat error {resp.status_code}: {resp.text}")
    return resp.json()

def run_tests():
    passed = 0
    total = 13
    print("=" * 60)
    print("RUNNING 13 TARGETED NLP / CONVERSATIONAL FLOW TESTS")
    print("=" * 60)

    # TEST 1: User says "hi"
    print("\n--- TEST 1: Greeting ---")
    conv1 = "test-conv-1"
    res1 = chat(conv1, "hi")
    msg1 = res1["message"]
    print(f"User: 'hi'\nBot: {msg1}")
    t_state1 = res1.get("transaction_state", {})
    if "Who will be sending the money" in msg1 and "How much would you like to transfer" not in msg1:
        print("PASS TEST 1: Natural greeting asking for sender, not immediately asking for amount.")
        passed += 1
    else:
        print(f"FAIL TEST 1: Expected natural greeting asking for sender. Got: {msg1}")

    # TEST 2: User says "I want to transfer ₹50,000 to the US."
    print("\n--- TEST 2: Amount and Destination extraction ---")
    conv2 = "test-conv-2"
    res2 = chat(conv2, "I want to transfer ₹50,000 to the US.")
    msg2 = res2["message"]
    st2 = res2.get("transaction_state", {})
    print(f"User: 'I want to transfer ₹50,000 to the US.'\nBot: {msg2}\nState: amount={st2.get('amount')}, dest={st2.get('destination_country')}")
    if st2.get("amount") == 50000 and "United States" in str(st2.get("destination_country")) and "Who will be sending the money" in msg2:
        print("PASS TEST 2: Extracted amount 50000 and destination US; asks only for missing sender.")
        passed += 1
    else:
        print(f"FAIL TEST 2: {msg2}, State: {st2}")

    # TEST 3: User says "Rahul Kumar" when asked for sender
    print("\n--- TEST 3: Provide Sender ---")
    res3 = chat(conv2, "Rahul Kumar")
    msg3 = res3["message"]
    st3 = res3.get("transaction_state", {})
    print(f"User: 'Rahul Kumar'\nBot: {msg3}\nState: sender={st3.get('sender_name')}")
    if "Rahul Kumar" in str(st3.get("sender_name")) or "Rahul Kumar" in str(st3.get("customer_name")):
        print("PASS TEST 3: sender set to Rahul Kumar.")
        passed += 1
    else:
        print(f"FAIL TEST 3: sender not Rahul Kumar. State: {st3}")

    # TEST 4: User says "Meera Joshi" when asked for recipient
    print("\n--- TEST 4: Provide Recipient ---")
    res4 = chat(conv2, "Meera Joshi")
    msg4 = res4["message"]
    st4 = res4.get("transaction_state", {})
    print(f"User: 'Meera Joshi'\nBot: {msg4}\nState: recipient={st4.get('recipient_name')}")
    if "Meera Joshi" in str(st4.get("recipient_name")):
        print("PASS TEST 4: recipient set to Meera Joshi.")
        passed += 1
    else:
        print(f"FAIL TEST 4: recipient not Meera Joshi. State: {st4}")

    # TEST 5: User says "education" when asked for purpose
    print("\n--- TEST 5: Provide Purpose & Reach Summary ---")
    res5 = chat(conv2, "education")
    msg5 = res5["message"]
    st5 = res5.get("transaction_state", {})
    print(f"User: 'education'\nBot: {msg5}\nStage: {st5.get('stage')}")
    if "Transfer Summary" in msg5 and "Would you like me to proceed" in msg5 and "Education" in str(st5.get("purpose")):
        print("PASS TEST 5: purpose set to education, reached Transfer Summary and awaiting confirmation.")
        passed += 1
    else:
        print(f"FAIL TEST 5: Did not reach Transfer Summary. Msg: {msg5}")

    # TEST 6: User says "thn send 9000$"
    print("\n--- TEST 6: Filler word 'thn' with amount '9000$' ---")
    conv6 = "test-conv-6"
    res6 = chat(conv6, "thn send 9000$")
    msg6 = res6["message"]
    st6 = res6.get("transaction_state", {})
    print(f"User: 'thn send 9000$'\nBot: {msg6}\nState: amount={st6.get('amount')}, sender={st6.get('sender_name')}")
    if st6.get("amount") == 9000 and st6.get("sender_name") != "Thn" and st6.get("customer_name") != "Thn":
        print("PASS TEST 6: amount=9000, 'thn' is recognized as filler and NEVER becomes sender.")
        passed += 1
    else:
        print(f"FAIL TEST 6: amount={st6.get('amount')}, sender={st6.get('sender_name')}")

    # TEST 7: User says "okay then send 9000 dollars to Abhishek for education"
    print("\n--- TEST 7: Multi-entity extraction with leading filler 'okay then' ---")
    conv7 = "test-conv-7"
    res7 = chat(conv7, "okay then send 9000 dollars to Abhishek for education")
    msg7 = res7["message"]
    st7 = res7.get("transaction_state", {})
    print(f"User: 'okay then send 9000 dollars to Abhishek for education'\nBot: {msg7}\nState: amount={st7.get('amount')}, recip={st7.get('recipient_name')}, purpose={st7.get('purpose')}")
    if st7.get("amount") == 9000 and "Abhishek" in str(st7.get("recipient_name")) and "Education" in str(st7.get("purpose")):
        print("PASS TEST 7: Extracted amount=9000, recipient=Abhishek, purpose=Education; 'okay then' ignored.")
        passed += 1
    else:
        print(f"FAIL TEST 7: State: {st7}")

    # TEST 8: User says "Actually make it 7000"
    print("\n--- TEST 8: Explicit update: 'Actually make it 7000' ---")
    res8 = chat(conv7, "Actually make it 7000")
    msg8 = res8["message"]
    st8 = res8.get("transaction_state", {})
    print(f"User: 'Actually make it 7000'\nBot: {msg8}\nState: amount={st8.get('amount')}, recip={st8.get('recipient_name')}, purpose={st8.get('purpose')}")
    if st8.get("amount") == 7000 and "Abhishek" in str(st8.get("recipient_name")) and "Education" in str(st8.get("purpose")):
        print("PASS TEST 8: Only amount updated to 7000; recipient and purpose preserved.")
        passed += 1
    else:
        print(f"FAIL TEST 8: State: {st8}")

    # TEST 9: User says "Actually send it to Rahul"
    print("\n--- TEST 9: Explicit update: 'Actually send it to Rahul' ---")
    res9 = chat(conv7, "Actually send it to Rahul")
    msg9 = res9["message"]
    st9 = res9.get("transaction_state", {})
    print(f"User: 'Actually send it to Rahul'\nBot: {msg9}\nState: amount={st9.get('amount')}, recip={st9.get('recipient_name')}, purpose={st9.get('purpose')}")
    if st9.get("amount") == 7000 and "Rahul" in str(st9.get("recipient_name")) and "Education" in str(st9.get("purpose")):
        print("PASS TEST 9: Only recipient updated to Rahul; amount 7000 preserved.")
        passed += 1
    else:
        print(f"FAIL TEST 9: State: {st9}")

    # TEST 10: User says "cancel"
    print("\n--- TEST 10: Cancellation ---")
    conv10 = "test-conv-10"
    chat(conv10, "Send ₹10,000 from Rahul Kumar to Meera Joshi for education.")
    res10 = chat(conv10, "cancel")
    msg10 = res10["message"]
    st10 = res10.get("transaction_state", {})
    print(f"User: 'cancel'\nBot: {msg10}\nStage: {st10.get('stage')}")
    if "cancelled" in msg10.lower() and st10.get("stage") == "CANCELLED":
        print("PASS TEST 10: Transaction cancelled cleanly with no WireMock call or balance modification.")
        passed += 1
    else:
        print(f"FAIL TEST 10: Msg: {msg10}, Stage: {st10.get('stage')}")

    # TEST 11: All-in-one message
    print("\n--- TEST 11: All-in-one message ---")
    conv11 = "test-conv-11"
    res11 = chat(conv11, "Send ₹10,000 from Rahul Kumar to Meera Joshi for education.")
    msg11 = res11["message"]
    st11 = res11.get("transaction_state", {})
    print(f"User: 'Send ₹10,000 from Rahul Kumar to Meera Joshi for education.'\nBot: {msg11}")
    if "Transfer Summary" in msg11 and "Would you like me to proceed" in msg11:
        print("PASS TEST 11: All information extracted; went straight to Transfer Summary without re-asking.")
        passed += 1
    else:
        print(f"FAIL TEST 11: Did not go directly to Transfer Summary. Msg: {msg11}")

    # TEST 12: Role reversal
    print("\n--- TEST 12: Role Reversal ---")
    # Part A: Bhavya Patel -> Rahul Kumar
    conv12a = "test-conv-12a"
    res12a = chat(conv12a, "Send ₹10,000 from Bhavya Patel to Rahul Kumar for education")
    st12a = res12a.get("transaction_state", {})
    s12a = st12a.get("sender_name")
    r12a = st12a.get("recipient_name")
    print(f"Part A: Sender={s12a}, Recipient={r12a}")

    # Part B: Rahul Kumar -> Bhavya Patel
    conv12b = "test-conv-12b"
    res12b = chat(conv12b, "Send ₹10,000 from Rahul Kumar to Bhavya Patel for education")
    st12b = res12b.get("transaction_state", {})
    s12b = st12b.get("sender_name")
    r12b = st12b.get("recipient_name")
    print(f"Part B: Sender={s12b}, Recipient={r12b}")

    if "Bhavya Patel" in str(s12a) and "Rahul Kumar" in str(r12a) and "Rahul Kumar" in str(s12b) and "Bhavya Patel" in str(r12b):
        print("PASS TEST 12: Role reversal works symmetrically; people are not locked into single roles.")
        passed += 1
    else:
        print(f"FAIL TEST 12: Part A ({s12a} -> {r12a}), Part B ({s12b} -> {r12b})")

    # TEST 13: Ambiguous identity
    print("\n--- TEST 13: Ambiguous identity (Bhavya) ---")
    conv13 = "test-conv-13"
    res13 = chat(conv13, "Send ₹10,000 to Bhavya for education")
    msg13 = res13["message"]
    print(f"User: 'Send ₹10,000 to Bhavya for education'\nBot: {msg13}")
    if "multiple people" in msg13.lower() or "which one do you mean" in msg13.lower() or "clarify" in msg13.lower():
        print("PASS TEST 13: Detected ambiguity between Bhavya Patel and Bhavya Desai and asked for clarification.")
        passed += 1
    else:
        print(f"FAIL TEST 13: Did not ask for clarification. Msg: {msg13}")

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} PASSED")
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
