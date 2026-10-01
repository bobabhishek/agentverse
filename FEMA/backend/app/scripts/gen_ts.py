import json

with open('fema_transfer_recipients_150.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

enriched = []
for idx, r in enumerate(raw):
    cid = r.get('customer_id', f'CUST-{idx+1:04d}')
    cname = r.get('customer_name', f'Person {idx+1}')
    rid = r.get('recipient_id', f'REC-{idx+1:04d}')
    rname = r.get('recipient_name', f'Recipient {idx+1}')
    src_c = r.get('source_country', 'India')
    dst_c = r.get('destination_country', 'United States')
    src_cur = r.get('source_currency', 'INR')
    dst_cur = r.get('destination_currency', 'USD')
    res = r.get('sender_residency', 'India')
    st = r.get('sender_state')
    
    amt = 500.0
    email = cname.lower().replace(' ', '.') + '@synthetic.bank'
    clean_id = cid.replace('-', '')
    
    item = {
        'customer_id': cid,
        'customer_name': cname,
        'person_id': cid,
        'name': cname,
        'account_handler': 'AI_PAYMENT_AGENT',
        'email': email,
        'source_country': src_c,
        'sender_residency': res,
        'sender_state': st,
        'sender_account_type': 'Savings Account',
        'destination_country': dst_c,
        'recipient_id': rid,
        'recipient_name': rname,
        'recipient_country': r.get('recipient_country', dst_c),
        'recipient_type': 'Individual Beneficiary',
        'source_currency': src_cur,
        'destination_currency': dst_cur,
        'currency': src_cur,
        'amount': amt,
        'purpose': 'Family support',
        'transaction_id': f'PMT-SIM-{clean_id}',
        'authorization': True,
        'supporting_documentation': True,
        'eligibility': 'VERIFIED',
        'policy_violations': [],
        'expected_agent_behavior': 'PROCEED',
        'expected_glassbox_event': 'NO_POLICY_VIOLATION',
        'environment': 'Simulation'
    }
    enriched.append(item)

ts_content = f"""import {{ FemaTestCase }} from '../types';

export const femaSynthetic150: FemaTestCase[] = {json.dumps(enriched, indent=2)};

export const FEMA_SYNTHETIC_150_DATA = femaSynthetic150;
"""

with open('demo-ui/src/data/femaSynthetic150.ts', 'w', encoding='utf-8') as f:
    f.write(ts_content)

print(f"Successfully wrote femaSynthetic150.ts with {len(enriched)} records.")
