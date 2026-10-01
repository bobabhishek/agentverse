import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { AgentHeader } from './components/AgentHeader';
import { ChatConsole } from './components/ChatConsole';
import { ComplianceDrawer } from './components/ComplianceDrawer';
import { HistorySidebar } from './components/HistorySidebar';
import { DocumentationView } from './components/DocumentationView';
import { DatabaseView } from './components/DatabaseView';
import { CrossBorderBackground } from './components/CrossBorderBackground';
import { femaSynthetic150 } from './data/femaSynthetic150';
import { FemaTestCase, ChatMessage, ConversationSession } from './types';
import { fetchTestCases, postChatMessage, fetchAccountBalances, downloadAuditTrailPdf } from './services/api';
import { SlidersHorizontal } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'agent' | 'database' | 'documentation'>('agent');
  const [testCases, setTestCases] = useState<FemaTestCase[]>(femaSynthetic150);
  const [selectedTestCase, setSelectedTestCase] = useState<FemaTestCase>(femaSynthetic150[0]);

  const [filterMode, setFilterMode] = useState<'all' | 'failures' | 'valid'>('all');

  const [senderCountry, setSenderCountry] = useState<'India' | 'United States'>('India');

  // Route direction: false = India -> US, true = US -> India
  const [isReverseRoute, setIsReverseRoute] = useState<boolean>(false);

  // Side Drawer visibility (hidden by default as requested!)
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);

  // Conversation history sidebar
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);

  // Real user conversations list - loaded from localStorage, no hardcoded dummy text
  const [conversations, setConversations] = useState<ConversationSession[]>(() => {
    try {
      localStorage.removeItem('fema_conversations_history');
      const saved = localStorage.getItem('fema_user_real_chats');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch (e) {
      console.error('Error reading saved conversations:', e);
    }
    return [];
  });

  // Active conversation ID
  const [activeConversationId, setActiveConversationId] = useState<string>(() => {
    return `chat-${Date.now()}`;
  });

  // Current active conversation's messages
  const currentConversation = conversations.find((c) => c.id === activeConversationId);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    return currentConversation?.messages || [];
  });

  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  // Dynamic Account Balances & Completed Audit Trails
  const [accountBalances, setAccountBalances] = useState<{
    sender: { INR: number; USD: number };
    completed_conversations: string[];
  }>({
    sender: { INR: 100000, USD: 10000 },
    completed_conversations: []
  });

  // Fetch balances on initial mount
  useEffect(() => {
    fetchAccountBalances()
      .then((data) => {
        if (data && data.sender) {
          setAccountBalances(data);
        }
      })
      .catch((err) => {
        console.warn('Could not fetch balances:', err);
      });
  }, []);

  // Ensure window is at top on refresh
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Fetch test cases from FastAPI backend
  useEffect(() => {
    fetchTestCases(filterMode)
      .then((data) => {
        if (data && data.length > 0) {
          setTestCases(data);
        }
      })
      .catch((err) => {
        console.warn('Backend test cases fetch warning, using local dataset:', err);
      });
  }, [filterMode]);

  // Sync conversations to localStorage whenever updated
  useEffect(() => {
    try {
      localStorage.setItem('fema_user_real_chats', JSON.stringify(conversations));
    } catch (e) {
      console.error('Error saving conversations:', e);
    }
  }, [conversations]);

  // Handle Sender Account Country Selection
  const handleSelectSenderCountry = (country: 'India' | 'United States') => {
    setSenderCountry(country);
    const isUS = country === 'United States';
    setIsReverseRoute(isUS);

    // Keep the current sender! Do not switch to a random person!
    // Update the country and currency context for the active sender.
    setSelectedTestCase((prev) => ({
      ...prev,
      source_country: country,
      currency: country === 'India' ? 'INR' : 'USD'
    }));
  };

  // When activeConversationId changes, load its messages & route
  const handleSelectConversation = (id: string) => {
    const target = conversations.find((c) => c.id === id);
    if (target) {
      setActiveConversationId(id);
      setMessages(target.messages);
      setIsReverseRoute(target.isReverseRoute);
      if (target.isReverseRoute) {
        setSenderCountry('United States');
      } else {
        setSenderCountry('India');
      }
      const tc = testCases.find((t) => t.person_id === target.testCaseId);
      if (tc) {
        setSelectedTestCase(tc);
      }
    }
  };

  // Start a New Chat
  const handleNewChat = () => {
    const newId = `chat-${Date.now()}`;
    setActiveConversationId(newId);
    setMessages([]);
    setIsEvaluating(false);
  };

  // Delete a conversation from Recents
  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      if (id === activeConversationId) {
        if (filtered.length > 0) {
          setActiveConversationId(filtered[0].id);
          setMessages(filtered[0].messages);
        } else {
          handleNewChat();
        }
      }
      return filtered;
    });
  };

  // Change Test Case
  const handleSelectTestCase = (tc: FemaTestCase) => {
    setSelectedTestCase(tc);
    if (tc.source_country === 'United States' || tc.currency === 'USD') {
      setSenderCountry('United States');
      setIsReverseRoute(true);
    } else {
      setSenderCountry('India');
      setIsReverseRoute(false);
    }
    setConversations((prev) =>
      prev.map((c) => (c.id === activeConversationId ? { ...c, testCaseId: tc.person_id } : c))
    );
  };

  // Toggle Route Direction (India <-> US)
  const handleToggleRoute = () => {
    setIsReverseRoute((prev) => {
      const next = !prev;
      setSenderCountry(next ? 'United States' : 'India');
      setConversations((all) =>
        all.map((c) => (c.id === activeConversationId ? { ...c, isReverseRoute: next } : c))
      );
      return next;
    });
  };

  // Generate clean conversation title from first user prompt
  const formatConversationTitle = (text: string) => {
    let clean = text.replace(/^(can you |please |transfer |send )/i, '');
    clean = clean.charAt(0).toUpperCase() + clean.slice(1);
    if (clean.length > 30) {
      return clean.slice(0, 28) + '...';
    }
    return clean || `Transaction $${selectedTestCase.amount}`;
  };

  // Send Message & Mock Autonomous Agent Response
  const handleSendMessage = (userText: string) => {
    const userMsgId = `user-${Date.now()}`;
    const userTimestamp = new Date().toLocaleTimeString();

    const newMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      timestamp: userTimestamp,
      text: userText
    };

    const updatedMessages = [...messages, newMsg];
    setMessages(updatedMessages);
    setIsEvaluating(true);

    // Detect if user specifically mentioned direction in their prompt
    const lowerText = userText.toLowerCase();
    let currentCountry: 'India' | 'United States' = senderCountry;
    let currentReverse = isReverseRoute;
    if (
      lowerText.includes('us to india') ||
      lowerText.includes('from my us account') ||
      lowerText.includes('from the us') ||
      lowerText.includes('from us account')
    ) {
      currentCountry = 'United States';
      currentReverse = true;
      setSenderCountry('United States');
      setIsReverseRoute(true);
    } else if (
      lowerText.includes('india to us') ||
      lowerText.includes('from my india account') ||
      lowerText.includes('from india account') ||
      lowerText.includes('from india')
    ) {
      currentCountry = 'India';
      currentReverse = false;
      setSenderCountry('India');
      setIsReverseRoute(false);
    }

    const sourceCountry = currentCountry;
    const destCountry = selectedTestCase.destination_country || (currentCountry === 'India' ? 'United States' : 'India');
    const remittanceTypeName = sourceCountry === destCountry
      ? `Domestic ${sourceCountry === 'India' ? 'INR' : 'USD'} transfer`
      : currentReverse
      ? 'Cross-border inward remittance (FIRC / Inbound FEMA)'
      : 'Cross-border outward remittance (LRS / Outbound FEMA)';

    // Save user message to conversations list
    setConversations((prev) => {
      const exists = prev.some((c) => c.id === activeConversationId);
      if (exists) {
        return prev.map((c) =>
          c.id === activeConversationId
            ? { ...c, messages: updatedMessages }
            : c
        );
      } else {
        // First message of this new conversation session -> create entry in Recents!
        const newSession: ConversationSession = {
          id: activeConversationId,
          title: formatConversationTitle(userText),
          createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          testCaseId: selectedTestCase.person_id,
          isReverseRoute: currentReverse,
          messages: updatedMessages
        };
        return [newSession, ...prev];
      }
    });

    // Send request to FastAPI backend
    postChatMessage(userText, selectedTestCase.person_id, activeConversationId, currentReverse, currentCountry)
      .then((backendResp) => {
        const isCompleted = backendResp.next_action === 'COMPLETED' || (!backendResp.next_action && (backendResp.policy?.checks?.length ?? 0) > 0);
        const checkItems = (isCompleted && backendResp.policy?.checks) ? backendResp.policy.checks.map((chk) => ({
          name: chk.name,
          status: (chk.status === 'PASS' ? 'pass' : 'fail') as 'pass' | 'fail',
          detail: chk.reason
        })) : [];

        const targetPersonId = backendResp.transaction_state?.person_id || backendResp.transaction_state?.customer_id;
        const targetPersonName = backendResp.transaction_state?.customer_name;
        if (targetPersonName) {
          setSelectedTestCase((prev) => ({
            ...prev,
            name: targetPersonName,
            customer_name: targetPersonName,
            person_id: targetPersonId || prev.person_id,
            source_country: backendResp.transaction_state?.source_country || prev.source_country,
            destination_country: backendResp.transaction_state?.destination_country || prev.destination_country,
            recipient_name: backendResp.transaction_state?.recipient_name || prev.recipient_name,
            recipient_id: backendResp.transaction_state?.recipient_id || prev.recipient_id,
            currency: backendResp.transaction_state?.source_currency || prev.currency,
          }));
        } else if (targetPersonId) {
          const matched = testCases.find((tc) => tc.person_id === targetPersonId);
          if (matched && matched.person_id !== selectedTestCase.person_id) {
            setSelectedTestCase(matched);
          }
        }

        const agentMsg: ChatMessage = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString(),
          text: backendResp.message,
          structuredEval: (isCompleted && checkItems.length > 0) ? {
            identifiedType: backendResp.policy?.identified_type || remittanceTypeName,
            sourceToDest: backendResp.policy?.source_to_dest || `${sourceCountry} → ${destCountry}`,
            checks: checkItems,
            rogueAction: backendResp.decision?.type === 'PROCEED_DESPITE_POLICY_FAILURE',
            rogueSummary: backendResp.decision?.summary
          } : undefined,
          transfer: isCompleted ? backendResp.transfer : undefined,
          events: isCompleted ? backendResp.events : undefined
        };

        const finalMessages = [...updatedMessages, agentMsg];
        setMessages(finalMessages);

        if (backendResp.account_balances) {
          setAccountBalances(backendResp.account_balances);
        }

        const isTransferSuccess = Boolean(backendResp.transfer?.success);

        setConversations((prev) =>
          prev.map((c) => {
            if (c.id === activeConversationId) {
              return {
                ...c,
                messages: finalMessages,
                hasAuditTrail: c.hasAuditTrail || isTransferSuccess
              };
            }
            return c;
          })
        );

        setIsEvaluating(false);
      })
      .catch((err) => {
        console.error('Backend connection error:', err);
        const errMsg: ChatMessage = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString(),
          text: `I encountered an issue connecting to the FEMA agent backend (${err.message || 'connection failed'}). Please ensure the backend server is running on http://127.0.0.1:8000.`
        };
        const finalMessages = [...updatedMessages, errMsg];
        setMessages(finalMessages);
        setIsEvaluating(false);
      });
  };

  const failureCount = selectedTestCase.policy_violations.length;

  const handleDownloadAuditTrail = (convId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    downloadAuditTrailPdf(convId, `audit-trail-${convId}.pdf`).catch((err) => {
      console.error('Audit trail download error:', err);
      alert(err.message || 'Audit trail not available for this session');
    });
  };

  return (
    <div className="h-screen bg-[#08090c] text-slate-100 flex flex-col font-sans selection:bg-slate-700 selection:text-white overflow-hidden">
      {/* Navigation Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedTestCase={selectedTestCase}
        onOpenDrawer={() => setIsDrawerOpen(true)}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      {/* Main Workspace Layout (Sidebar + Chat Console / Database / Documentation) */}
      <CrossBorderBackground className="flex-1">
        <div className="flex-1 flex overflow-hidden w-full h-full relative">
          {/* Conversation History Sidebar */}
          {activeTab === 'agent' && (
            <HistorySidebar
              isOpen={isSidebarOpen}
              onToggle={() => setIsSidebarOpen((prev) => !prev)}
              conversations={conversations}
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onNewChat={handleNewChat}
              onDeleteConversation={handleDeleteConversation}
              onOpenInspector={() => setIsDrawerOpen(true)}
              completedConversations={accountBalances.completed_conversations}
              onDownloadAuditTrail={handleDownloadAuditTrail}
            />
          )}

          {/* Center Main Content Area */}
          <main className="flex-1 flex flex-col min-h-0 bg-transparent overflow-hidden">
            {activeTab === 'documentation' ? (
              <div className="flex-1 overflow-y-auto bg-transparent">
                <DocumentationView />
              </div>
            ) : activeTab === 'database' ? (
              <DatabaseView />
            ) : (
              /* Operational Agent Layout — Edge-to-Edge ChatGPT Style */
              <div className="flex-1 flex flex-col min-h-0 w-full h-full relative">
                <AgentHeader
                  onNewChat={handleNewChat}
                  senderCountry={senderCountry}
                  onSelectSenderCountry={handleSelectSenderCountry}
                  activeSenderName={selectedTestCase.customer_name || selectedTestCase.name}
                  balances={accountBalances.sender}
                />
                <ChatConsole
                  activeTestCase={selectedTestCase}
                  senderCountry={senderCountry}
                  isReverseRoute={isReverseRoute}
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  isEvaluating={isEvaluating}
                  onOpenDrawer={() => setIsDrawerOpen(true)}
                />
              </div>
            )}
          </main>
        </div>
      </CrossBorderBackground>

      {/* Floating Side Dock Icon to open hidden Test Case & Policy drawer */}
      {activeTab === 'agent' && (
        <button
          onClick={() => setIsDrawerOpen(true)}
          title="Open Test Case, Transaction & Policy Checks"
          className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-black/50 hover:bg-black/70 backdrop-blur-md border-l border-y border-white/[0.12] hover:border-blue-500/50 py-3.5 px-2 rounded-l-2xl flex flex-col items-center gap-2.5 shadow-2xl transition-all cursor-pointer group"
        >
          <SlidersHorizontal className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
          <span className="text-[10px] font-mono tracking-widest uppercase text-slate-300 [writing-mode:vertical-rl] rotate-180">
            Inspector
          </span>
          <span
            className={`w-2 h-2 rounded-full ${failureCount > 0 ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'
              }`}
          />
        </button>
      )}

      {/* Collapsible Slide-over Drawer for Test Case, Transaction, and Policy Checks */}
      <ComplianceDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        testCases={testCases}
        selectedTestCase={selectedTestCase}
        onSelectTestCase={handleSelectTestCase}
        filterMode={filterMode}
        setFilterMode={setFilterMode}
        isReverseRoute={isReverseRoute}
        onToggleRoute={handleToggleRoute}
        balances={accountBalances.sender}
      />

      {/* Footer bar */}
      {(activeTab === 'documentation' || activeTab === 'database') && (
        <footer className="shrink-0 border-t border-slate-800/80 bg-[#08090c] py-2 px-6 text-center text-xs font-mono text-slate-500">
          FEMA Guardrail Test Bench · Single Autonomous Rogue AI Compliance Prototype · SQLite Persistent Source of Truth
        </footer>
      )}
    </div>
  );
};
export default App;
