export interface FemaTestCase {
  person_id: string;
  name: string;
  email: string;
  source_country: string;
  sender_residency: string;
  sender_account_type: string;
  destination_country: string;
  recipient_type: string;
  recipient_name: string;
  transaction_id: string;
  amount: number;
  currency: string;
  purpose: string;
  authorization: boolean;
  supporting_documentation: boolean;
  eligibility: 'VERIFIED' | 'NOT_VERIFIED';
  policy_violations: string[];
  expected_agent_behavior: 'PROCEED_ROGUE_TEST' | 'PROCEED';
  expected_glassbox_event: 'POLICY_VIOLATION' | 'NO_POLICY_VIOLATION';
  environment: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  timestamp: string;
  text: string;
  structuredEval?: {
    identifiedType: string;
    sourceToDest: string;
    checks: {
      name: string;
      status: 'pass' | 'fail';
      detail: string;
    }[];
    rogueAction: boolean;
    rogueSummary?: string;
  };
  transfer?: {
    success: boolean;
    gateway: string;
    environment: string;
    status: string;
    payment_id?: string;
    error?: string;
  };
  events?: {
    event_type: string;
    timestamp: string;
    transaction_id: string;
    person_id: string;
    details?: Record<string, any>;
  }[];
}

export interface ConversationSession {
  id: string;
  title: string;
  createdAt: string;
  testCaseId: string;
  isReverseRoute: boolean;
  messages: ChatMessage[];
}
