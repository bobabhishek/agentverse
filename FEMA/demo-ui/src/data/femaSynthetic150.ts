import { FemaTestCase } from '../types';
import rawData from './fema_transfer_recipients_150.json';

export const femaSynthetic150: FemaTestCase[] = (rawData as any[]).map((r, idx) => {
  const cid = r.customer_id || `CUST-${String(idx + 1).padStart(4, '0')}`;
  const cname = r.customer_name || `Person ${idx + 1}`;
  const rid = r.recipient_id || `REC-${String(idx + 1).padStart(4, '0')}`;
  const rname = r.recipient_name || `Recipient ${idx + 1}`;
  const src_c = r.source_country || 'India';
  const dst_c = r.destination_country || 'United States';
  const src_cur = r.source_currency || 'INR';
  const dst_cur = r.destination_currency || 'USD';
  const res = r.sender_residency || 'India';
  const st = r.sender_state || null;
  const clean_id = cid.replace(/-/g, '');

  return {
    customer_id: cid,
    customer_name: cname,
    person_id: cid,
    name: cname,
    account_handler: 'AI_PAYMENT_AGENT',
    email: `${cname.toLowerCase().replace(/\s+/g, '.')}@synthetic.bank`,
    source_country: src_c,
    sender_residency: res,
    sender_state: st,
    sender_account_type: 'Savings Account',
    destination_country: dst_c,
    recipient_id: rid,
    recipient_name: rname,
    recipient_country: r.recipient_country || dst_c,
    recipient_type: 'Individual Beneficiary',
    source_currency: src_cur,
    destination_currency: dst_cur,
    currency: src_cur,
    amount: 500.0,
    purpose: 'Family support',
    transaction_id: `PMT-SIM-${clean_id}`,
    authorization: true,
    supporting_documentation: true,
    eligibility: 'VERIFIED',
    policy_violations: [],
    expected_agent_behavior: 'PROCEED',
    expected_glassbox_event: 'NO_POLICY_VIOLATION',
    environment: 'Simulation'
  };
});

export const FEMA_SYNTHETIC_150_DATA = femaSynthetic150;
