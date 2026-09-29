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
  reverseRoute?: boolean
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
      reverse_route: reverseRoute
    })
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Server error: ${res.status}`);
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
