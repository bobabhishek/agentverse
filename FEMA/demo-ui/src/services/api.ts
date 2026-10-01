import { FemaTestCase } from '../types';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://127.0.0.1:8000';

export interface ChatApiResponse {
  conversation_id: string;
  message: string;
  next_action?: string;
  transaction_state?: Record<string, any>;
  agent?: {
    name: string;
    status: string;
    type: string;
  };
  policy?: {
    status: 'VIOLATION' | 'COMPLIANT';
    failure_count: number;
    checks: {
      name: string;
      check: string;
      status: string;
      reason: string;
    }[];
    identified_type: string;
    source_to_dest: string;
  };
  decision?: {
    decision: string;
    type: string;
    policy_status: string;
    violations: string[];
    action: string;
    tool_called: boolean;
    summary: string;
  };
  transaction?: Record<string, any>;
  transfer?: {
    success: boolean;
    gateway: string;
    environment: string;
    status: string;
    payment_id?: string;
    error?: string;
    raw_response?: Record<string, any>;
  };
  events?: {
    event_type: string;
    timestamp: string;
    transaction_id: string;
    person_id: string;
    details?: Record<string, any>;
  }[];
  account_balances?: {
    sender: { INR: number; USD: number };
    completed_conversations: string[];
  };
  audit_trail?: Record<string, any>;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { method: 'GET' });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}

export async function fetchTestCases(status: string = 'all'): Promise<FemaTestCase[]> {
  const res = await fetch(`${API_BASE}/api/test-cases?status=${encodeURIComponent(status)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch test cases: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTestCase(personId: string, reverseRoute: boolean = false): Promise<any> {
  const res = await fetch(`${API_BASE}/api/test-cases/${encodeURIComponent(personId)}?reverse_route=${reverseRoute}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch test case ${personId}: ${res.statusText}`);
  }
  return res.json();
}

export async function postChatMessage(
  message: string,
  personId: string,
  conversationId?: string,
  reverseRoute?: boolean,
  sourceCountry?: string,
  destinationCountry?: string,
  recipientName?: string
): Promise<ChatApiResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      person_id: personId,
      conversation_id: conversationId,
      reverse_route: reverseRoute,
      source_country: sourceCountry,
      destination_country: destinationCountry,
      recipient_name: recipientName
    })
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Server error: ${res.status}`);
  }

  return res.json();
}

export async function createSyntheticPerson(data: {
  name: string;
  country: string;
  initial_inr?: number;
  initial_usd?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/database/create-person`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to create synthetic person');
  }

  return res.json();
}

export async function postSimulationRun(
  personId: string,
  message?: string,
  reverseRoute?: boolean
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/simulation/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      person_id: personId,
      message,
      reverse_route: reverseRoute
    })
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Simulation run failed: ${res.status}`);
  }

  return res.json();
}

export async function fetchAccountBalances(): Promise<{
  sender: { INR: number; USD: number };
  completed_conversations: string[];
}> {
  const res = await fetch(`${API_BASE}/api/accounts/balance`);
  if (!res.ok) {
    throw new Error(`Failed to fetch balances: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDatabaseSummary(): Promise<{
  total_customers: number;
  total_recipients: number;
  total_accounts: number;
  total_transactions: number;
  last_updated: string;
  database_type: string;
  database_file: string;
}> {
  const res = await fetch(`${API_BASE}/api/database/summary`);
  if (!res.ok) throw new Error(`Failed to fetch database summary: ${res.statusText}`);
  return res.json();
}

export async function fetchDatabaseCustomers(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/database/customers`);
  if (!res.ok) throw new Error(`Failed to fetch database customers: ${res.statusText}`);
  return res.json();
}

export async function fetchDatabaseRecipients(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/database/recipients`);
  if (!res.ok) throw new Error(`Failed to fetch database recipients: ${res.statusText}`);
  return res.json();
}

export async function fetchDatabaseAccounts(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/database/accounts`);
  if (!res.ok) throw new Error(`Failed to fetch database accounts: ${res.statusText}`);
  return res.json();
}

export async function fetchDatabaseTransactions(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/database/transactions`);
  if (!res.ok) throw new Error(`Failed to fetch database transactions: ${res.statusText}`);
  return res.json();
}

export async function downloadAuditTrailPdf(conversationId: string, filename?: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/audit-trail/${encodeURIComponent(conversationId)}/download`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Audit trail not available for this session');
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || `audit-trail-${conversationId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}


