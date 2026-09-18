'use client';

import { useState, useRef, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  ShieldAlert, 
  Database, 
  Send, 
  Plus, 
  User, 
  Bot, 
  AlertTriangle, 
  Trash2, 
  MessageSquare, 
  Pencil, 
  Check,
  Terminal,
  Zap,
  Info,
  FileText,
  Download,
  ArrowRight,
  ArrowLeft
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import syntheticData from '@/data/synthetic-customers.json';

type LogType = {
  id: string;
  role: 'user' | 'agent1' | 'agent2';
  content: string;
  timestamp: string;
  type?: 'info' | 'warning' | 'error' | 'success';
  customerData?: any;
};

type ChatSession = {
  id: string;
  title: string;
  logs: LogType[];
  timestamp: number;
};

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeNode, setActiveNode] = useState<'idle' | 'agent1' | 'agent2'>('idle');
  const [lastContext, setLastContext] = useState<any>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const auditScrollRef = useRef<HTMLDivElement>(null);

  // Renaming state
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Quick prompt presets
  const quickPrompts = [
    "I need Emma Evans phone number",
    "Get details for Hans Russo",
    "Show all customers in Amsterdam",
    "Show cancelled orders",
    "What is the GPS of id SYN-CUST-1003?",
    "Find customer John Doe"
  ];

  // Load sessions from local storage on mount
  useEffect(() => {
    setIsMounted(true);
    const saved = localStorage.getItem('chatSessions');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSessions(parsed);
        if (parsed.length > 0) {
          setCurrentSessionId(parsed[0].id);
        }
      } catch (e) {
        console.error("Failed to parse sessions", e);
      }
    }
  }, []);

  // Save sessions to local storage when they change
  useEffect(() => {
    if (isMounted) {
      localStorage.setItem('chatSessions', JSON.stringify(sessions));
    }
  }, [sessions, isMounted]);

  const currentLogs = sessions.find(s => s.id === currentSessionId)?.logs || [];

  // Auto-scroll to bottom of chat and audit trail
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
    if (auditScrollRef.current) {
      auditScrollRef.current.scrollTop = auditScrollRef.current.scrollHeight;
    }
  }, [currentLogs, isProcessing]);

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const formatTime = () => {
    const d = new Date();
    return d.toTimeString().split(' ')[0]; // HH:MM:SS
  };

  const executeSimulation = async (queryText: string) => {
    if (!queryText.trim() || isProcessing) return;

    const userQuery = queryText.trim();
    setInputText('');
    setIsProcessing(true);

    let activeSessionId = currentSessionId;
    
    // If no active session, create one
    if (!activeSessionId) {
      activeSessionId = Math.random().toString(36).substring(7);
      const newSession: ChatSession = {
        id: activeSessionId,
        title: userQuery.length > 25 ? userQuery.substring(0, 25) + '...' : userQuery,
        logs: [],
        timestamp: Date.now(),
      };
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(activeSessionId);
    }

    const addLog = (log: Omit<LogType, 'id' | 'timestamp'>) => {
      const newLog: LogType = { 
        ...log, 
        id: Math.random().toString(36).substring(7), 
        timestamp: formatTime() 
      };
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, logs: [...s.logs, newLog] };
        }
        return s;
      }));
    };

    // 1. Log USER input event
    addLog({ 
      role: 'user', 
      content: `Prompt received by Agent 2 (India): "${userQuery}"`, 
      type: 'info' 
    });
    
    await sleep(500);

    const normalize = (str: string) => str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const queryLower = userQuery.toLowerCase().trim();
    const normalizedQuery = normalize(userQuery);

    // 1. Greetings check
    const greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good evening', 'sup', 'howdy'];
    if (greetings.includes(queryLower)) {
      addLog({ 
        role: 'agent2', 
        content: "Hello! I am Agent 2 (India Node). How can I assist you with European customer data today?", 
        type: 'info' 
      });
      setIsProcessing(false);
      return;
    }

    // 2. Thank you / Polite closing check
    const thankYouPhrases = ['thanks', 'thank you', 'thx', 'cheers', 'awesome', 'great thanks', 'thank u', 'thanks agent', 'ok thanks', 'okay thanks'];
    if (thankYouPhrases.some(phrase => queryLower.includes(phrase))) {
      addLog({ 
        role: 'agent2', 
        content: "You're welcome! Let me know if you need any more European customer records or telemetry checks.", 
        type: 'info' 
      });
      setIsProcessing(false);
      return;
    }

    // 3. Frustration / Error report check
    if (queryLower.includes('wrong') || queryLower.includes('doesnt match') || queryLower.includes('doesn\'t match') || 
        queryLower.includes('mistake') || queryLower.includes('stupid') || queryLower.includes('fix this') || queryLower.includes('wtf')) {
      addLog({ 
        role: 'agent2', 
        content: "Apologies for the issue! Please specify an exact customer ID (e.g. SYN-CUST-1003), customer name, city, country, or status, and I will fetch the data from Agent 1.", 
        type: 'info' 
      });
      setIsProcessing(false);
      return;
    }

    // Intent & Attribute extraction
    const wantsPhone = queryLower.includes('phone');
    const wantsAddress = queryLower.includes('address') || queryLower.includes('location');
    const wantsGps = queryLower.includes('gps') || queryLower.includes('coordinates');
    const wantsStatus = queryLower.includes('status') || queryLower.includes('order');

    // Asking for details / profile
    const isAskingForDetails = queryLower.includes('detail') || queryLower.includes('all') || queryLower.includes('everything') || queryLower.includes('profile') || queryLower.includes('info');
    
    // wantsId is ONLY true if user asks specifically for ID (e.g. "what is the id of Hans") and NOT asking for details/everything
    const wantsId = (queryLower.includes('customer id') || queryLower.includes('what is the id') || queryLower === 'id') && !isAskingForDetails;

    // Fetch all if details requested, or if no specific single attribute filter requested
    const fetchAll = isAskingForDetails || (!wantsPhone && !wantsAddress && !wantsGps && !wantsId && !wantsStatus);

    // Check if an unavailable field (security number, dob, ssn, passport, etc.) was asked
    const checkUnavailableField = () => {
      if (queryLower.includes('security')) return 'Security Number';
      if (queryLower.includes('ssn')) return 'SSN';
      if (queryLower.includes('dob') || queryLower.includes('date of birth')) return 'Date of Birth';
      if (queryLower.includes('salary')) return 'Salary';
      if (queryLower.includes('passport')) return 'Passport Number';
      if (queryLower.includes('credit card')) return 'Credit Card';
      return null;
    };
    const unavailableField = checkUnavailableField();

    // Check if query is a follow-up referencing previous context (e.g. "that id", "additional details", "her address")
    const isFollowUp = queryLower.includes('her ') || 
                      queryLower.includes('his ') || 
                      queryLower.includes('their ') || 
                      queryLower.includes('that id') || 
                      queryLower.includes('that customer') || 
                      queryLower.includes('this customer') || 
                      queryLower.includes('that record') || 
                      queryLower.includes('additional detail') || 
                      queryLower.includes('more detail') || 
                      queryLower === 'details' || 
                      queryLower === 'more details' || 
                      queryLower === 'all details' || 
                      queryLower === 'address' || 
                      queryLower === 'gps' || 
                      queryLower === 'phone';

    // 4. Search for Single Customer Match in syntheticData
    let targetCustomer: any = null;

    // Check exact ID match like SYN-CUST-1003 or 1003
    const idMatch = queryLower.match(/syn-cust-\d{4}/i);
    if (idMatch) {
      const fullId = idMatch[0].toUpperCase();
      targetCustomer = syntheticData.find(c => c.id.toUpperCase() === fullId);
    }

    if (!targetCustomer) {
      const numMatch = queryLower.match(/\b1\d{3}\b/);
      if (numMatch) {
        const targetId = `SYN-CUST-${numMatch[0]}`;
        targetCustomer = syntheticData.find(c => c.id.toUpperCase() === targetId);
      }
    }

    // Check full name match in synthetic database
    if (!targetCustomer) {
      targetCustomer = syntheticData.find(c => {
        const normName = normalize(c.name);
        return normalizedQuery.includes(normName);
      });
    }

    // Follow-up context fallback ONLY if query is a follow-up and no new specific name/ID was found
    if (!targetCustomer && isFollowUp && lastContext && lastContext.type === 'single') {
      targetCustomer = lastContext.customer;
    }

    // 5. Check ID Range match (e.g. SYN-CUST-1001 to SYN-CUST-1010 or 1001 to 1005)
    let rangeGroup: any[] = [];
    let rangeLabel = "";
    const rangeMatch = queryLower.match(/(?:syn-cust-)?(\d{4})\s*(?:to|-|through)\s*(?:syn-cust-)?(\d{4})/i);
    if (rangeMatch && !targetCustomer) {
      const startNum = parseInt(rangeMatch[1], 10);
      const endNum = parseInt(rangeMatch[2], 10);
      if (!isNaN(startNum) && !isNaN(endNum)) {
        const min = Math.min(startNum, endNum);
        const max = Math.max(startNum, endNum);
        rangeGroup = syntheticData.filter(c => {
          const num = parseInt(c.id.replace("SYN-CUST-", ""), 10);
          return num >= min && num <= max;
        });
        if (rangeGroup.length > 0) {
          rangeLabel = `range SYN-CUST-${min} to SYN-CUST-${max}`;
        }
      }
    }

    // 6. Group matches by Country, City, or Status
    if (!targetCustomer && rangeGroup.length === 0) {
      const allCountries = Array.from(new Set(syntheticData.map(c => normalize(c.country))));
      const allCities = Array.from(new Set(syntheticData.map(c => normalize(c.city))));
      const allStatuses = Array.from(new Set(syntheticData.map(c => normalize(c.order_status))));

      let matchedGroup: any[] = [];
      let groupCategory = "";
      let groupValue = "";

      for (const c of allCountries) {
        if (normalizedQuery.includes(c)) {
          matchedGroup = syntheticData.filter(cust => normalize(cust.country) === c);
          groupCategory = "country";
          groupValue = syntheticData.find(cust => normalize(cust.country) === c)?.country || c;
          break;
        }
      }

      if (matchedGroup.length === 0) {
        for (const c of allCities) {
          if (normalizedQuery.includes(c)) {
            matchedGroup = syntheticData.filter(cust => normalize(cust.city) === c);
            groupCategory = "city";
            groupValue = syntheticData.find(cust => normalize(cust.city) === c)?.city || c;
            break;
          }
        }
      }

      if (matchedGroup.length === 0) {
        for (const c of allStatuses) {
          if (normalizedQuery.includes(c)) {
            matchedGroup = syntheticData.filter(cust => normalize(cust.order_status) === c);
            groupCategory = "order status";
            groupValue = syntheticData.find(cust => normalize(cust.order_status) === c)?.order_status || c;
            break;
          }
        }
      }

      if (matchedGroup.length > 0) {
        rangeGroup = matchedGroup;
        rangeLabel = `${groupCategory} ${groupValue}`;
      }
    }

    // Handle Bulk / Range Results
    if (rangeGroup.length > 0 && !targetCustomer) {
      setLastContext({ type: 'bulk', matchedGroup: rangeGroup, groupCategory: "selection", groupValue: rangeLabel });
      
      setActiveNode('agent2');
      addLog({
        role: 'agent2',
        content: `[No Direct DB Access] Received user request: "${userQuery}". Agent 2 sending A2A request to Agent 1 (Europe Node)...`,
        type: 'info',
      });
      await sleep(1500);
      
      setActiveNode('agent1');
      addLog({
        role: 'agent1',
        content: `[EU DB Read] Agent 1 queried local database for ${rangeLabel} (${rangeGroup.length} records). Transmitting raw sensitive data to Agent 2 (India)...`,
        type: 'warning',
      });
      await sleep(1200);

      setActiveNode('agent2');
      addLog({
        role: 'agent2',
        content: `Agent 2 received response from Agent 1 and rendered it to the user.`,
        type: 'info',
        customerData: {
          isBulk: true,
          groupCategory: "selection",
          groupValue: rangeLabel,
          records: rangeGroup
        }
      });
      
      await sleep(400);
      setActiveNode('idle');
      setIsProcessing(false);
      return;
    }

    // Handle Unmatched Query (Clean target extraction)
    if (!targetCustomer) {
      setActiveNode('agent2');
      addLog({
        role: 'agent2',
        content: `[No Direct DB Access] Received user request: "${userQuery}". Agent 2 sending A2A request to Agent 1 (Europe Node)...`,
        type: 'info',
      });
      await sleep(1200);

      setActiveNode('agent1');
      addLog({
        role: 'agent1',
        content: `[EU DB Read] Agent 1 queried local database. 0 records found for query "${userQuery}".`,
        type: 'warning',
      });
      await sleep(1000);

      // Clean extraction of query subject (e.g. "what about id 4nm21ai072" -> "4nm21ai072")
      const cleanTarget = userQuery.replace(/what about id:?/i, '').replace(/what about/i, '').replace(/id:?/i, '').trim() || userQuery;

      setActiveNode('agent2');
      addLog({ 
        role: 'agent2', 
        content: `No customer record matching '${cleanTarget}' was found in the European database.`, 
        type: 'error' 
      });
      setActiveNode('idle');
      setIsProcessing(false);
      return;
    }

    // Handle Unavailable Field requested for an existing customer
    if (unavailableField && !wantsPhone && !wantsAddress && !wantsGps && !wantsId && !wantsStatus && !isAskingForDetails) {
      setActiveNode('agent2');
      addLog({
        role: 'agent2',
        content: `[No Direct DB Access] Received user request: "${userQuery}". Agent 2 sending A2A request to Agent 1 (Europe Node)...`,
        type: 'info',
      });
      await sleep(1200);

      setActiveNode('agent1');
      addLog({
        role: 'agent1',
        content: `[EU DB Read] Agent 1 queried local database for ${targetCustomer.name} (${targetCustomer.id}). Field '${unavailableField}' is not stored in the database.`,
        type: 'warning',
      });
      await sleep(1000);

      setActiveNode('agent2');
      addLog({ 
        role: 'agent2', 
        content: `Requested field '${unavailableField}' is not available for ${targetCustomer.name} (${targetCustomer.id}) in the European database.\nAvailable fields: ID, Name, Country, City, Address, Phone, GPS, Order Status.`, 
        type: 'error' 
      });
      setActiveNode('idle');
      setIsProcessing(false);
      return;
    }

    // Handle Single Customer Matched Result
    setLastContext({ type: 'single', customer: targetCustomer });

    setActiveNode('agent2');
    addLog({
      role: 'agent2',
      content: `[No Direct DB Access] Received user request: "${userQuery}". Agent 2 sending A2A request to Agent 1 (Europe Node)...`,
      type: 'info',
    });

    await sleep(1500);

    setActiveNode('agent1');
    const requestedFields = [];
    if (wantsPhone) requestedFields.push('phone');
    if (wantsAddress) requestedFields.push('address');
    if (wantsGps) requestedFields.push('gps');
    if (wantsStatus) requestedFields.push('order status');
    if (wantsId) requestedFields.push('id');
    const fieldsLabel = (fetchAll || requestedFields.length === 0) ? '[full profile]' : `[${requestedFields.join(', ')}]`;

    addLog({
      role: 'agent1',
      content: `[EU DB Read] Agent 1 queried local database for ${targetCustomer.name} (${targetCustomer.id}). Transmitting raw sensitive data ${fieldsLabel} to Agent 2 (India)...`,
      type: 'warning',
    });

    await sleep(1200);

    setActiveNode('agent2');
    addLog({
      role: 'agent2',
      content: `Agent 2 received response from Agent 1 and rendered it to the user.`,
      type: 'info',
      customerData: {
        isBulk: false,
        customer: targetCustomer,
        wantsPhone,
        wantsAddress,
        wantsGps,
        wantsStatus,
        wantsId,
        fetchAll
      }
    });

    await sleep(400);
    setActiveNode('idle');
    setIsProcessing(false);
  };

  const downloadAuditTrailJSON = () => {
    if (currentLogs.length === 0) return;

    const formattedExport = currentLogs.map(log => ({
      event_id: log.id,
      timestamp: log.timestamp,
      role: log.role,
      node: log.role === 'agent2' ? 'Agent 2 (India)' : log.role === 'agent1' ? 'Agent 1 (Europe)' : 'User',
      event_type: log.type ? log.type.toUpperCase() : 'INFO',
      message: log.content,
      payload: log.customerData || null
    }));

    const jsonString = JSON.stringify(formattedExport, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-trail-${currentSessionId || 'session'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSimulation(inputText);
  };

  const deleteSession = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setSessions(prev => prev.filter(s => s.id !== id));
    if (currentSessionId === id) {
      setCurrentSessionId(null);
    }
  };

  const startEditing = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.title);
  };

  const saveEdit = (e?: React.FormEvent | React.FocusEvent | React.MouseEvent) => {
    if (e && 'stopPropagation' in e) e.stopPropagation();
    if (e && 'preventDefault' in e) e.preventDefault();
    if (editTitle.trim() && editingSessionId) {
      setSessions(prev => prev.map(s => s.id === editingSessionId ? { ...s, title: editTitle.trim() } : s));
    }
    setEditingSessionId(null);
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setActiveNode('idle');
    setIsProcessing(false);
    setLastContext(null);
  };

  // Metrics computation
  const totalMsgs = currentLogs.filter(l => l.role === 'user' || l.role === 'agent2').length;
  const totalEvents = currentLogs.length;
  const totalHops = currentLogs.filter(l => l.role === 'agent1' || l.role === 'agent2').length;

  if (!isMounted) return null;

  return (
    <div className="h-screen w-full flex bg-[#030712] text-slate-200 font-sans overflow-hidden selection:bg-emerald-500/30">
      
      {/* 1. Left Navigation Sidebar */}
      <aside className="w-64 shrink-0 h-full border-r border-slate-800/80 bg-[#070c18] flex flex-col p-4">
        
        {/* Brand Header */}
        <div className="flex items-center gap-3 mb-6 px-1">
          <div className="w-9 h-9 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-sm">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-semibold text-slate-100 text-sm tracking-tight">A2A Guard</h1>
            <p className="text-[10px] font-mono text-slate-500 tracking-wider uppercase font-semibold">SOVEREIGNTY MONITOR</p>
          </div>
        </div>

        {/* New Simulation Button */}
        <Button 
          onClick={startNewChat}
          className="w-full justify-start gap-2 bg-[#0b1325] hover:bg-[#121c33] text-slate-200 border border-slate-800 text-xs font-medium py-2.5 mb-6 rounded-lg shadow-sm"
        >
          <Plus className="w-4 h-4 text-slate-400" />
          New simulation
        </Button>

        {/* Sessions Section */}
        <div className="flex-1 flex flex-col min-h-0">
          <h2 className="text-[10px] font-mono text-slate-500 font-semibold uppercase tracking-wider mb-2 px-1">
            SESSIONS
          </h2>
          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {sessions.length === 0 ? (
              <div className="text-xs text-slate-600 font-mono px-1 py-2">
                No active sessions.
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => !isProcessing && setCurrentSessionId(session.id)}
                  className={`group flex items-center justify-between px-2.5 py-2 rounded-lg cursor-pointer text-xs transition-colors border ${
                    currentSessionId === session.id
                      ? 'bg-[#11192e] text-slate-100 border-slate-700/80'
                      : 'text-slate-400 hover:bg-[#0b1325] hover:text-slate-300 border-transparent'
                  }`}
                >
                  {editingSessionId === session.id ? (
                    <div className="flex items-center w-full gap-1">
                      <Input
                        autoFocus
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && saveEdit(e)}
                        onBlur={(e) => saveEdit(e)}
                        onClick={(e) => e.stopPropagation()}
                        className="h-6 text-xs px-1.5 bg-slate-900 border-slate-700 focus-visible:ring-emerald-500/50 text-slate-200"
                      />
                      <button onClick={(e) => saveEdit(e)} className="p-1 hover:text-emerald-400">
                        <Check className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 truncate">
                        <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                        <span className="truncate">{session.title}</span>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => startEditing(e, session)}
                          className="p-1 text-slate-500 hover:text-emerald-400"
                          title="Rename"
                        >
                          <Pencil className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => deleteSession(e, session.id)}
                          className="p-1 text-slate-500 hover:text-red-400"
                          title="Delete"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="pt-3 border-t border-slate-800/80 mt-auto text-[11px] font-mono text-slate-500 leading-tight space-y-0.5">
          <p>Synthetic dataset • {syntheticData.length} EU profiles</p>
          <p>Stored locally in this browser</p>
        </div>
      </aside>

      {/* 2. Main Work Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full p-6 overflow-hidden">
        
        {/* Top Header Bar */}
        <header className="flex items-center justify-between mb-5 shrink-0">
          <div>
            <h2 className="text-xl font-semibold text-slate-100 tracking-tight">A2A Simulation</h2>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-[#0b1325] border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300 flex items-center gap-1.5 shadow-sm">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>{totalMsgs} msgs</span>
              <span className="text-slate-600">•</span>
              <span>{totalEvents} events</span>
            </div>
          </div>
        </header>

        {/* Top Section: A2A Telemetry Channel */}
        <section className="bg-[#070c18] border border-slate-800/90 rounded-xl p-5 mb-5 shrink-0 shadow-sm relative overflow-hidden">
          
          {/* Channel Header Bar */}
          <div className="flex items-center justify-end mb-3 font-mono text-xs">
            {activeNode !== 'idle' ? (
              <span className="text-amber-400 flex items-center gap-1.5 font-semibold">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping inline-block" />
                REQUEST IN FLIGHT
              </span>
            ) : (
              <span className="text-slate-500 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-600 inline-block" />
                CHANNEL IDLE
              </span>
            )}
          </div>

          {/* Telemetry Canvas Grid */}
          <div className="bg-telemetry-grid bg-[#0a0f1d] border border-slate-800/80 rounded-xl p-6 flex items-center justify-between relative">
            
            {/* Left Node: Agent 2 (India) */}
            <div className={`w-64 bg-[#070c18] border transition-all duration-300 rounded-xl p-4 relative ${
              activeNode === 'agent2' ? 'border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.2)]' : 'border-slate-800'
            }`}>
              <div className="flex justify-between items-start mb-2">
                <div className="w-8 h-8 rounded-lg bg-amber-950/80 border border-amber-800 flex items-center justify-center text-amber-400">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <Badge className="bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-mono px-2 py-0.5 font-bold">
                  IN
                </Badge>
              </div>
              <h3 className="text-sm font-semibold text-slate-100">Agent 2 • India Node</h3>
              <p className="text-xs text-amber-400 font-mono mt-0.5">Non-compliant • External</p>
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] font-mono text-slate-500">
                No direct DB access
              </div>
            </div>

            {/* Center Connection Track - SPACED DUAL TRACKS */}
            <div className="flex-1 px-8 flex flex-col items-center justify-center relative py-2 gap-6">
              
              {/* Top Track: Request Path (Agent 2 [IN, Left] -> Agent 1 [EU, Right]) */}
              <div className="w-full relative flex items-center justify-center">
                <div className={`w-full h-0.5 border-b border-dashed transition-colors duration-300 ${
                  activeNode === 'agent2' ? 'border-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 'border-slate-700/80'
                }`} />
                <div className="absolute left-1/2 -translate-x-1/2">
                  <Badge className={`text-[11px] font-mono px-3 py-0.5 rounded-full flex items-center gap-1 transition-all ${
                    activeNode === 'agent2' 
                      ? 'bg-amber-950 text-amber-400 border border-amber-800 shadow-[0_0_10px_rgba(245,158,11,0.3)] animate-pulse' 
                      : 'bg-[#0a0f1d] text-slate-500 border border-slate-800'
                  }`}>
                    Request <ArrowRight className="w-3 h-3" />
                  </Badge>
                </div>
              </div>

              {/* Bottom Track: Data Path (Agent 1 [EU, Right] -> Agent 2 [IN, Left]) */}
              <div className="w-full relative flex items-center justify-center">
                <div className={`w-full h-0.5 border-b border-dashed transition-colors duration-300 ${
                  activeNode === 'agent1' ? 'border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'border-slate-700/80'
                }`} />
                <div className="absolute left-1/2 -translate-x-1/2">
                  <Badge className={`text-[11px] font-mono px-3 py-0.5 rounded-full flex items-center gap-1 transition-all ${
                    activeNode === 'agent1' 
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800 shadow-[0_0_10px_rgba(16,185,129,0.3)] animate-pulse' 
                      : 'bg-[#0a0f1d] text-slate-500 border border-slate-800'
                  }`}>
                    <ArrowLeft className="w-3 h-3" /> Data
                  </Badge>
                </div>
              </div>

            </div>

            {/* Right Node: Agent 1 (Europe) */}
            <div className={`w-64 bg-[#070c18] border transition-all duration-300 rounded-xl p-4 relative ${
              activeNode === 'agent1' ? 'border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'border-slate-800'
            }`}>
              <div className="flex justify-between items-start mb-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800 flex items-center justify-center text-emerald-400">
                  <Database className="w-4 h-4" />
                </div>
                <Badge className="bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-mono px-2 py-0.5 font-bold">
                  EU
                </Badge>
              </div>
              <h3 className="text-sm font-semibold text-slate-100">Agent 1 • Europe Node</h3>
              <p className="text-xs text-emerald-400 font-mono mt-0.5">Attested • GDPR compliant</p>
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] font-mono text-slate-500">
                Exclusive local DB access
              </div>
            </div>

          </div>
        </section>

        {/* Bottom Section: Split Workspace (Console + Audit Trail) */}
        <div className="flex-1 flex gap-5 min-h-0 overflow-hidden">
          
          {/* Left Column: Agent 2 Console */}
          <div className="flex-1 bg-[#070c18] border border-slate-800 rounded-xl flex flex-col overflow-hidden shadow-sm">
            
            {/* Console Header */}
            <div className="px-4 py-3 border-b border-slate-800/90 bg-[#090e1c] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-amber-500" />
                <h3 className="font-semibold text-slate-200 text-sm">Agent 2 console</h3>
                <Badge className="bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-mono px-1.5 py-0.2">
                  IN
                </Badge>
              </div>
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                USER → EXTERNAL NODE
              </span>
            </div>

            {/* Console Main Content */}
            <div className="flex-1 overflow-y-auto p-5 scroll-smooth" ref={chatScrollRef}>
              
              {!currentSessionId || currentLogs.filter(l => l.role === 'user' || l.role === 'agent2').length === 0 ? (
                /* Empty Console State with Quick Prompt Chips */
                <div className="h-full flex flex-col items-center justify-center text-center p-6 my-auto">
                  <h3 className="text-base font-semibold text-slate-100 mb-1">Ask the India node for EU customer data</h3>
                  <p className="text-xs text-slate-400 max-w-md mb-8 leading-relaxed">
                    Agent 2 has no database access and must route every request through Agent 1 in Europe. Watch what crosses the border.
                  </p>
                  
                  {/* Preset Prompt Pills */}
                  <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                    {quickPrompts.map((promptText, idx) => (
                      <button
                        key={idx}
                        onClick={() => executeSimulation(promptText)}
                        disabled={isProcessing}
                        className="bg-[#0b1325] hover:bg-[#121c33] text-slate-300 border border-slate-800/90 hover:border-slate-700 text-xs px-3.5 py-2.5 rounded-full text-left font-mono transition-all shadow-sm truncate hover:text-slate-100 disabled:opacity-50"
                      >
                        {promptText}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                /* Active Chat Log */
                <div className="space-y-4">
                  {currentLogs.map((log) => {
                    if (log.role === 'user') {
                      return (
                        <div key={log.id} className="flex justify-end">
                          <div className="flex items-center gap-2 max-w-[85%]">
                            <div className="bg-[#0e172a] border border-slate-700/80 text-slate-200 text-xs rounded-xl px-4 py-2.5 shadow-sm">
                              {log.content.replace(/^Prompt received by Agent 2 \(India\): "/, '').replace(/"$/, '')}
                            </div>
                            <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
                              <User className="w-3.5 h-3.5 text-slate-300" />
                            </div>
                          </div>
                        </div>
                      );
                    }

                    if (log.role === 'agent2' && log.customerData) {
                      const data = log.customerData;
                      return (
                        <div key={log.id} className="flex justify-start items-start gap-3">
                          <div className="w-7 h-7 rounded-full bg-amber-950/80 border border-amber-800 flex items-center justify-center shrink-0 text-amber-400">
                            <ShieldAlert className="w-3.5 h-3.5" />
                          </div>
                          
                          {data.isBulk ? (
                            /* Bulk Data List Card */
                            <div className="bg-[#0a0f1d] border border-slate-800/90 rounded-xl p-4 text-xs font-mono text-slate-300 max-w-md w-full space-y-2 shadow-sm">
                              <div className="font-semibold text-slate-100 text-sm border-b border-slate-800 pb-2">
                                Records for {data.groupValue} ({data.records.length} matches)
                              </div>
                              <div className="max-h-48 overflow-y-auto space-y-1 text-slate-400 pr-1">
                                {data.records.map((r: any, idx: number) => (
                                  <div key={idx} className="flex justify-between border-b border-slate-800/40 py-1">
                                    <span className="text-slate-200">{r.name} ({r.id})</span>
                                    <span className="text-slate-500">{r.city}, {r.country}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : (
                            /* Single Customer Profile Card */
                            <div className="bg-[#0a0f1d] border border-slate-800/90 rounded-xl p-4 text-xs font-mono text-slate-300 max-w-md w-full space-y-1.5 shadow-sm">
                              <div className="font-semibold text-slate-100 text-sm mb-2 block border-b border-slate-800 pb-2">
                                {data.customer.name}
                              </div>
                              {(data.wantsId || data.fetchAll) && (
                                <div><span className="text-slate-500 font-semibold">ID:</span> <span className="text-slate-300">{data.customer.id}</span></div>
                              )}
                              <div><span className="text-slate-500 font-semibold">Region:</span> <span className="text-slate-300">{data.customer.city}, {data.customer.country}</span></div>
                              {(data.wantsPhone || data.fetchAll) && (
                                <div><span className="text-slate-500 font-semibold">Phone:</span> <span className="text-slate-300">{data.customer.phone}</span></div>
                              )}
                              {(data.wantsAddress || data.fetchAll) && (
                                <div><span className="text-slate-500 font-semibold">Address:</span> <span className="text-slate-300">{data.customer.address}</span></div>
                              )}
                              {(data.wantsGps || data.fetchAll) && (
                                <div><span className="text-slate-500 font-semibold">GPS:</span> <span className="text-slate-300">{data.customer.gps}</span></div>
                              )}
                              {(data.wantsStatus || data.fetchAll) && (
                                <div><span className="text-slate-500 font-semibold">Order status:</span> <span className="text-slate-300">{data.customer.order_status}</span></div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    }

                    if (log.role === 'agent2' && !log.customerData && !log.content.includes("Received user request")) {
                      return (
                        <div key={log.id} className="flex justify-start items-start gap-3">
                          <div className="w-7 h-7 rounded-full bg-amber-950/80 border border-amber-800 flex items-center justify-center shrink-0 text-amber-400">
                            <ShieldAlert className="w-3.5 h-3.5" />
                          </div>
                          <div className="bg-[#0a0f1d] border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-slate-300">
                            {log.content}
                          </div>
                        </div>
                      );
                    }

                    return null;
                  })}

                  {/* Loading Indicator */}
                  {isProcessing && (
                    <div className="flex justify-start items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-amber-950/80 border border-amber-800 flex items-center justify-center shrink-0 text-amber-400">
                        <ShieldAlert className="w-3.5 h-3.5" />
                      </div>
                      <div className="bg-[#0a0f1d] border border-slate-800/90 rounded-xl px-4 py-2.5 text-xs font-mono text-slate-400 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping inline-block" />
                        <span>Routing through Agent 1...</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>

            {/* Input Form */}
            <div className="p-3 bg-[#080d1a] border-t border-slate-800/90 shrink-0">
              <form onSubmit={handleFormSubmit} className="flex gap-2 items-center">
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="e.g. What is her address?"
                  className="flex-1 bg-[#0a0f1d] border-slate-800 text-slate-100 text-xs placeholder:text-slate-600 focus-visible:ring-emerald-500/40 rounded-lg h-9"
                  disabled={isProcessing}
                />
                <Button 
                  type="submit" 
                  disabled={isProcessing || !inputText.trim()} 
                  className="bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg h-9 w-9 p-0 flex items-center justify-center shrink-0 shadow-sm transition-colors"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>

          </div>

          {/* Right Column: Audit Trail */}
          <div className="w-[360px] lg:w-[400px] shrink-0 bg-[#070c18] border border-slate-800 rounded-xl flex flex-col overflow-hidden shadow-sm">
            
            {/* Audit Header */}
            <div className="px-4 py-3 border-b border-slate-800/90 bg-[#090e1c] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-500" />
                <h3 className="font-semibold text-slate-200 text-sm">Audit trail</h3>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-[10px]">
                <Button
                  onClick={downloadAuditTrailJSON}
                  disabled={currentLogs.length === 0}
                  variant="outline"
                  size="sm"
                  className="h-6 bg-[#0b1325] hover:bg-[#121c33] border-slate-800 text-slate-300 text-[10px] px-2 gap-1"
                  title="Download JSON Audit Log"
                >
                  <Download className="w-3 h-3 text-emerald-400" />
                  JSON
                </Button>
                <Badge variant="outline" className="bg-slate-900 border-slate-800 text-slate-400 px-1.5 py-0.2">
                  {totalEvents} EVENTS
                </Badge>
                <Badge variant="outline" className="bg-emerald-950/60 border-emerald-800 text-emerald-400 px-1.5 py-0.2">
                  {totalHops} HOPS
                </Badge>
              </div>
            </div>

            {/* Audit Log Stream - PURE AGENT TO AGENT LOG */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2.5 font-mono text-xs" ref={auditScrollRef}>
              {currentLogs.length === 0 ? (
                /* Empty Audit Trail State */
                <div className="h-full flex flex-col items-center justify-center text-center p-6 opacity-60 my-auto">
                  <Bot className="w-8 h-8 text-slate-600 mb-2" />
                  <p className="text-xs text-slate-500 max-w-[200px] leading-relaxed">
                    Immutable log is empty. Run a prompt to begin capturing telemetry.
                  </p>
                </div>
              ) : (
                currentLogs.map((log) => {
                  let styleClass = "bg-[#0a0f1d] border-slate-800/80 text-slate-300";
                  let headerBadge = null;

                  if (log.role === 'user') {
                    styleClass = "bg-[#0a0f1d] border-slate-800/80 text-slate-300";
                    headerBadge = (
                      <span className="text-slate-400 font-semibold flex items-center gap-1">
                        <Info className="w-3.5 h-3.5 text-slate-500" /> USER
                      </span>
                    );
                  } else if (log.role === 'agent2') {
                    styleClass = "bg-[#0a0f1d] border-amber-950 text-amber-200/90";
                    headerBadge = (
                      <span className="text-amber-400 font-semibold flex items-center gap-1">
                        <Info className="w-3.5 h-3.5 text-amber-500" /> AGENT 2 • IN
                      </span>
                    );
                  } else if (log.role === 'agent1') {
                    styleClass = "bg-amber-950/20 border-amber-700/50 text-amber-300/90";
                    headerBadge = (
                      <span className="text-amber-400 font-semibold flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> AGENT 1 • EU
                      </span>
                    );
                  }

                  return (
                    <div 
                      key={log.id} 
                      className={`p-3 rounded-lg border text-[11px] leading-relaxed transition-all shadow-sm ${styleClass}`}
                    >
                      <div className="flex justify-between items-center mb-1.5 text-[10px]">
                        {headerBadge}
                        <span className="text-slate-500 font-mono">{log.timestamp}</span>
                      </div>
                      <p className="break-words">{log.content}</p>
                    </div>
                  );
                })
              )}
            </div>

          </div>

        </div>

      </main>

    </div>
  );
}
