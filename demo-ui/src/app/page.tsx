'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { 
  Database, 
  Send, 
  Plus, 
  User, 
  Bot, 
  Trash2, 
  MessageSquare, 
  Pencil, 
  Check, 
  Sparkles,
  ArrowRight,
  Activity,
  ChevronRight,
  X,
  FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

type LogType = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
};

type ActivityStep = {
  node: string;
  title: string;
  description: string;
  badge: string;
  color: 'blue' | 'purple' | 'emerald';
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
  const [flowStage, setFlowStage] = useState<'idle' | 'requesting' | 'processing' | 'received' | 'completed'>('idle');
  const [isActivityOpen, setIsActivityOpen] = useState(true);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Renaming state
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Agent 1 Accuracy metric state (single source of truth: backend /api/agent-accuracy)
  const [agent1Accuracy, setAgent1Accuracy] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/agent-accuracy')
      .then(res => res.json())
      .then(data => {
        if (data && data.accuracy) {
          setAgent1Accuracy(data.accuracy);
        }
      })
      .catch(err => {
        console.error('Failed to fetch Agent 1 accuracy:', err);
      });
  }, []);

  // Quick prompt presets (clean, conversational queries)
  const quickPrompts = [
    "Give me the phone number for customer 1006.",
    "Give me customer names and order status.",
    "Show me the names of all customers.",
    "Show me the current status of customer 1006.",
    "Give me the address of customer 1006.",
    "Get details for Hans Russo"
  ];

  // 3-step minimal A2A activity trail
  const activitySteps: ActivityStep[] = [
    {
      node: "Agent 2 • India Node",
      title: "Request Sent",
      description: "User prompt formulated and routed across borders to Europe.",
      badge: "Step 1",
      color: "blue"
    },
    {
      node: "Agent 1 • Europe Node",
      title: "Request Processed",
      description: "Isolated synthetic customer records queried securely.",
      badge: "Step 2",
      color: "purple"
    },
    {
      node: "Agent 2 • India Node",
      title: "Response Received",
      description: "Cross-border customer payload delivered and response rendered.",
      badge: "Step 3",
      color: "emerald"
    }
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

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [currentLogs, isProcessing]);

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const formatTime = () => {
    const d = new Date();
    return d.toTimeString().split(' ')[0].slice(0, 5); // HH:MM
  };

  const createNewSession = (initialQuery?: string) => {
    const newId = Math.random().toString(36).substring(7);
    const newSession: ChatSession = {
      id: newId,
      title: initialQuery ? (initialQuery.length > 25 ? initialQuery.substring(0, 25) + '...' : initialQuery) : 'New Conversation',
      logs: [],
      timestamp: Date.now(),
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newId);
    return newId;
  };

  const deleteSession = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setSessions(prev => prev.filter(s => s.id !== id));
    if (currentSessionId === id) {
      const remaining = sessions.filter(s => s.id !== id);
      setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  const startEditing = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.title);
  };

  const saveEdit = (e?: React.SyntheticEvent) => {
    e?.stopPropagation();
    if (!editTitle.trim()) return;
    setSessions(prev => prev.map(s => s.id === editingSessionId ? { ...s, title: editTitle.trim() } : s));
    setEditingSessionId(null);
  };

  const executeSimulation = async (queryText: string) => {
    if (!queryText.trim() || isProcessing) return;

    const userQuery = queryText.trim();
    setInputText('');
    setIsProcessing(true);

    let activeSessionId = currentSessionId;
    if (!activeSessionId) {
      activeSessionId = createNewSession(userQuery);
    }

    // Add user message to conversation
    const userMsg: LogType = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content: userQuery,
      timestamp: formatTime()
    };

    setSessions(prev => prev.map(s => {
      if (s.id === activeSessionId) {
        const isFirst = s.logs.length === 0;
        return {
          ...s,
          title: isFirst ? (userQuery.length > 25 ? userQuery.substring(0, 25) + '...' : userQuery) : s.title,
          logs: [...s.logs, userMsg]
        };
      }
      return s;
    }));

    // Step 1: Agent 2 sends request to Europe
    setActiveNode('agent2');
    setFlowStage('requesting');
    await sleep(650);

    try {
      // Step 2: Agent 1 processes request in Europe
      setActiveNode('agent1');
      setFlowStage('processing');
      const response = await fetch(`http://localhost:8000/api/simulations/${activeSessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userQuery })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      await sleep(500);

      // Step 3: Agent 2 receives response
      setActiveNode('agent2');
      setFlowStage('received');
      await sleep(550);

      // Determine the conversational reply text
      const renderedEvent = data.events?.find((e: any) => e.event_type === 'RESPONSE_RENDERED');
      const conversationalReply = data.response?.reply || renderedEvent?.metadata?.customerData?.reply || renderedEvent?.action_description || 'I have retrieved the requested information from the European node.';

      const assistantMsg: LogType = {
        id: Math.random().toString(36).substring(7),
        role: 'assistant',
        content: conversationalReply,
        timestamp: formatTime()
      };

      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, logs: [...s.logs, assistantMsg] };
        }
        return s;
      }));

    } catch (error: any) {
      const errorMsg: LogType = {
        id: Math.random().toString(36).substring(7),
        role: 'assistant',
        content: `I couldn't reach the Europe node. Please make sure the backend server is running on port 8000.`,
        timestamp: formatTime()
      };
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, logs: [...s.logs, errorMsg] };
        }
        return s;
      }));
    } finally {
      setActiveNode('idle');
      setFlowStage('completed');
      setIsProcessing(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSimulation(inputText);
  };

  if (!isMounted) return null;

  return (
    <div className="flex h-screen bg-[#070c1a] text-slate-100 antialiased font-sans overflow-hidden">
      
      {/* 1. Left Sidebar: Sessions Navigation */}
      <aside className="w-64 bg-[#090f22] border-r border-slate-800/80 flex flex-col p-4 shrink-0 select-none">
        
        {/* Brand & New Chat */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-semibold text-sm text-slate-100 tracking-tight">AgentVerse</h1>
            </div>
          </div>
        </div>

        <Button 
          onClick={() => createNewSession()}
          className="w-full bg-[#0d162e] hover:bg-blue-600/20 text-blue-300 hover:text-blue-200 border border-blue-500/30 text-xs font-medium py-2 rounded-xl flex items-center justify-center gap-2 shadow-sm transition-all mb-4"
        >
          <Plus className="w-3.5 h-3.5 text-blue-400" />
          <span>New Chat</span>
        </Button>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 px-2 py-1 font-semibold">
            Conversations
          </div>
          {sessions.length === 0 ? (
            <div className="text-xs text-slate-500 px-2 py-3 text-center italic">
              No conversations yet
            </div>
          ) : (
            sessions.map((session) => (
              <div 
                key={session.id}
                onClick={() => setCurrentSessionId(session.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition-all border ${
                  session.id === currentSessionId 
                    ? 'bg-[#121c38] text-blue-300 border-blue-500/40 shadow-sm' 
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border-transparent'
                }`}
              >
                {editingSessionId === session.id ? (
                  <div className="flex items-center gap-1.5 w-full">
                    <Input
                      autoFocus
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && saveEdit(e)}
                      onBlur={(e) => saveEdit(e)}
                      onClick={(e) => e.stopPropagation()}
                      className="h-6 text-xs px-1.5 bg-slate-900 border-slate-700 text-slate-200"
                    />
                    <button onClick={(e) => saveEdit(e)} className="p-1 hover:text-emerald-400">
                      <Check className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2 truncate">
                      <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-500 group-hover:text-blue-400 transition-colors" />
                      <span className="truncate">{session.title}</span>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => startEditing(e, session)}
                        className="p-1 text-slate-500 hover:text-blue-400"
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

        {/* Sidebar Footer */}
        <div className="pt-3 border-t border-slate-800/80 mt-auto text-[11px] text-slate-500 leading-tight space-y-1">
          <div className="flex items-center gap-1.5 text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Azure OpenAI Connected</span>
          </div>
          <p className="font-mono text-[10px] text-slate-600">GPT-4o &bull; GPT-5.4-mini</p>
        </div>
      </aside>

      {/* 2. Main Work Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full p-5 overflow-hidden">
        
        {/* Top Header Bar */}
        <header className="flex items-center justify-between mb-4 shrink-0 pb-3 border-b border-slate-800/70">
          <div className="flex items-center gap-2.5">
            <h1 className="text-lg font-bold tracking-tight flex items-center gap-2.5 text-slate-100">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)]"></span>
              </span>
              <span className="bg-gradient-to-r from-blue-400 via-indigo-200 to-sky-300 bg-clip-text text-transparent tracking-wide">
                A2A Active
              </span>
            </h1>
          </div>
          
          <div className="flex items-center gap-2">
            <Link
              href="/docs"
              className="h-8 px-3 inline-flex items-center gap-1.5 rounded-lg border border-slate-800 bg-[#0a1126] text-xs font-medium text-slate-300 hover:text-blue-300 hover:border-blue-700/60 hover:bg-blue-950/40 transition-all shadow-sm"
              title="View GDPR Cross-Border A2A Documentation"
            >
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              <span>Test Case Docs</span>
            </Link>

            <Button
              onClick={() => setIsActivityOpen(!isActivityOpen)}
              variant="outline"
              size="sm"
              className={`h-8 border text-xs gap-1.5 rounded-lg transition-all ${
                isActivityOpen 
                  ? 'bg-blue-950/60 text-blue-300 border-blue-700/60' 
                  : 'bg-[#0a1126] text-slate-300 border-slate-800 hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-3.5 h-3.5 text-blue-400" />
              <span>A2A Flow</span>
              <Badge className="bg-blue-900/60 text-blue-300 text-[9px] px-1 py-0 ml-0.5">
                3 Hops
              </Badge>
            </Button>
          </div>
        </header>

        {/* Top Section: Agent Nodes Communication Banner */}
        <section className="bg-gradient-to-r from-[#060c1d] via-[#091128] to-[#0e0a22] border border-slate-800/80 rounded-2xl p-3 sm:p-3.5 mb-4 shrink-0 shadow-md">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-3 sm:gap-4 w-full">
            
            {/* Left Node: Agent 2 (India) */}
            <div className={`flex items-center gap-3 bg-[#060b18] border transition-all duration-300 rounded-xl px-3.5 py-2.5 w-full lg:w-auto min-w-[225px] ${
              flowStage === 'requesting' || flowStage === 'received' 
                ? 'border-blue-500 shadow-[0_0_18px_rgba(59,130,246,0.3)] bg-blue-950/30' 
                : 'border-slate-800 hover:border-slate-700'
            }`}>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all ${
                flowStage === 'requesting' || flowStage === 'received'
                  ? 'bg-blue-600/30 border border-blue-500 text-blue-300 shadow-[0_0_12px_rgba(59,130,246,0.4)]'
                  : 'bg-blue-950/70 border border-blue-800/60 text-blue-400'
              }`}>
                <Bot className="w-5 h-5" />
              </div>
              <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-slate-100 truncate">Agent 2 • India Node</span>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${
                    flowStage === 'requesting' || flowStage === 'received' 
                      ? 'bg-blue-400 animate-ping' 
                      : flowStage === 'completed'
                      ? 'bg-emerald-400'
                      : 'bg-blue-400/80'
                  }`} />
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] text-slate-400">Requesting Agent</span>
                  <span className="text-[9px] px-1 py-0 rounded bg-blue-950/80 text-blue-300 border border-blue-800/50 font-mono">South India</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 mt-0.5">Zero direct DB access</span>
              </div>
            </div>

            {/* Center Dynamic Communication Conduit */}
            <div className="flex-1 px-2 sm:px-4 flex flex-col items-center justify-center gap-2.5 w-full max-w-md">
              {/* Request Conduit: Agent 2 (IN) -> Agent 1 (EU) */}
              <div className="w-full flex items-center justify-between text-[10px] font-mono gap-2">
                <div className="flex items-center gap-1 text-slate-300 font-medium shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  <span>Request</span>
                </div>
                <div className="flex-1 mx-1.5 h-2 bg-slate-900/90 border border-slate-800 rounded-full relative overflow-hidden flex items-center px-0.5">
                  {flowStage === 'requesting' ? (
                    <div className="h-1 w-14 rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-indigo-400 animate-beam-right shadow-[0_0_10px_rgba(59,130,246,0.9)]" />
                  ) : (
                    <div className="w-full flex items-center justify-around opacity-30 text-[8px] text-blue-400 tracking-widest select-none">
                      <span>›</span><span>›</span><span>›</span><span>›</span><span>›</span>
                    </div>
                  )}
                </div>
                <Badge variant="outline" className={`text-[9px] px-2 py-0 border transition-all shrink-0 ${
                  flowStage === 'requesting' 
                    ? 'bg-blue-950 text-blue-200 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.3)] animate-pulse' 
                    : 'bg-[#060b18] text-slate-400 border-slate-800'
                }`}>
                  {flowStage === 'requesting' ? 'IN → EU • Sending' : 'IN → EU'}
                </Badge>
              </div>

              {/* Response Conduit: Agent 1 (EU) -> Agent 2 (IN) */}
              <div className="w-full flex items-center justify-between text-[10px] font-mono gap-2">
                <div className="flex items-center gap-1 text-slate-300 font-medium shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span>Response</span>
                </div>
                <div className="flex-1 mx-1.5 h-2 bg-slate-900/90 border border-slate-800 rounded-full relative overflow-hidden flex items-center px-0.5">
                  {flowStage === 'received' ? (
                    <div className="h-1 w-14 rounded-full bg-gradient-to-r from-purple-500 via-emerald-400 to-cyan-400 animate-beam-left shadow-[0_0_10px_rgba(168,85,247,0.9)]" />
                  ) : flowStage === 'processing' ? (
                    <div className="w-full h-1 bg-gradient-to-r from-purple-600/40 via-purple-400/80 to-purple-600/40 animate-pulse rounded-full" />
                  ) : (
                    <div className="w-full flex items-center justify-around opacity-30 text-[8px] text-purple-400 tracking-widest select-none">
                      <span>‹</span><span>‹</span><span>‹</span><span>‹</span><span>‹</span>
                    </div>
                  )}
                </div>
                <Badge variant="outline" className={`text-[9px] px-2 py-0 border transition-all shrink-0 ${
                  flowStage === 'received' 
                    ? 'bg-purple-950 text-emerald-300 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)] animate-pulse'
                    : flowStage === 'processing'
                    ? 'bg-purple-950 text-purple-200 border-purple-500 animate-pulse'
                    : 'bg-[#060b18] text-slate-400 border-slate-800'
                }`}>
                  {flowStage === 'received' ? 'EU → IN • Delivered' : flowStage === 'processing' ? 'EU • Querying DB' : 'EU → IN'}
                </Badge>
              </div>
            </div>

            {/* Right Node: Agent 1 (Europe) */}
            <div className={`flex items-center gap-3 bg-[#060b18] border transition-all duration-300 rounded-xl px-3.5 py-2.5 w-full lg:w-auto min-w-[225px] ${
              flowStage === 'processing' 
                ? 'border-purple-500 shadow-[0_0_18px_rgba(168,85,247,0.3)] bg-purple-950/30' 
                : 'border-slate-800 hover:border-slate-700'
            }`}>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all ${
                flowStage === 'processing'
                  ? 'bg-purple-600/30 border border-purple-500 text-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.4)]'
                  : 'bg-purple-950/70 border border-purple-800/60 text-purple-400'
              }`}>
                <Database className="w-5 h-5" />
              </div>
              <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-slate-100 truncate">Agent 1 • Europe Node</span>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${
                    flowStage === 'processing' 
                      ? 'bg-purple-400 animate-ping' 
                      : flowStage === 'completed'
                      ? 'bg-emerald-400'
                      : 'bg-purple-400/80'
                  }`} />
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] text-slate-400">Data Provider</span>
                  <span className="text-[9px] px-1 py-0 rounded bg-purple-950/80 text-purple-300 border border-purple-800/50 font-mono">North Europe</span>
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] text-slate-400">Accuracy</span>
                  <span className="text-[10px] font-mono font-semibold text-purple-300 bg-purple-950/80 border border-purple-800/50 px-1.5 py-0.5 rounded">
                    {agent1Accuracy ?? '—'}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 mt-0.5">Exclusive local DB access</span>
              </div>
            </div>

          </div>
        </section>

        {/* Main Content Workspace: Chat + Collapsible A2A Activity Panel */}
        <div className="flex-1 flex gap-4 min-h-0 overflow-hidden">
          
          {/* Conversational AI Chat Window */}
          <div className="flex-1 bg-[#091124] border border-slate-800/90 rounded-2xl flex flex-col overflow-hidden shadow-sm">
            
            {/* Scrollable Conversation Stream */}
            <div className="flex-1 overflow-y-auto p-5 scroll-smooth space-y-4" ref={chatScrollRef}>
              
              {currentLogs.length === 0 ? (
                /* Empty Chat Greeting State */
                <div className="h-full flex flex-col items-center justify-center text-center p-6 my-auto">
                  <div className="w-12 h-12 rounded-2xl bg-blue-950/80 border border-blue-700/60 flex items-center justify-center text-blue-400 mb-3 shadow-md shadow-blue-500/10">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-100 mb-1">
                    How can I assist you with European customer data?
                  </h3>
                  <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
                    I am Agent 2 in South India. I formulate your request and coordinate with Agent 1 in North Europe to answer your questions accurately.
                  </p>
                  
                  {/* Preset Prompt Pills */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-2xl w-full">
                    {quickPrompts.map((promptText, idx) => (
                      <button
                        key={idx}
                        onClick={() => executeSimulation(promptText)}
                        disabled={isProcessing}
                        className="bg-[#060b18] hover:bg-[#0c1630] text-slate-300 hover:text-blue-300 border border-slate-800/90 hover:border-blue-500/40 text-xs px-3.5 py-2.5 rounded-xl text-left transition-all shadow-sm flex items-center justify-between group disabled:opacity-50 gap-2"
                      >
                        <span className="leading-snug">{promptText}</span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 shrink-0 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                /* Active Conversation Messages */
                currentLogs.map((log) => {
                  if (log.role === 'user') {
                    return (
                      <div key={log.id} className="flex justify-end">
                        <div className="flex items-start gap-2.5 max-w-[80%]">
                          <div className="bg-[#122347] border border-blue-600/40 text-slate-100 text-sm rounded-2xl px-4 py-3 shadow-sm">
                            {log.content}
                          </div>
                          <div className="w-8 h-8 rounded-full bg-blue-950 border border-blue-700 flex items-center justify-center shrink-0 text-blue-300">
                            <User className="w-4 h-4" />
                          </div>
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={log.id} className="flex justify-start items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-950/80 border border-blue-700/80 flex items-center justify-center shrink-0 text-blue-400 shadow-sm mt-0.5">
                        <Bot className="w-4 h-4" />
                      </div>
                      
                      <div className="space-y-1.5 max-w-2xl w-full">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-semibold text-blue-400">Agent 2 (India)</span>
                          <span className="text-[10px] text-slate-500 font-mono">{log.timestamp}</span>
                        </div>

                        <div className="bg-[#060b18] border border-slate-800/90 rounded-2xl p-4 text-slate-200 shadow-sm">
                          <FormattedMessage text={log.content} />
                        </div>
                      </div>
                    </div>
                  );
                })
              )}

              {/* In-flight Processing Loading State */}
              {isProcessing && (
                <div className="flex justify-start items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-950/80 border border-blue-700/80 flex items-center justify-center shrink-0 text-blue-400 animate-pulse">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-[#060b18] border border-slate-800 rounded-2xl px-4 py-3 text-xs text-slate-300 flex items-center gap-3 shadow-sm">
                    <div className="flex gap-1 items-center">
                      <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.3s]" />
                      <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.15s]" />
                      <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" />
                    </div>
                    <span>
                      {activeNode === 'agent1' 
                        ? "Agent 1 (Europe) processing query..." 
                        : "Agent 2 coordinating cross-border request..."}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-[#060b18] border-t border-slate-800/90 shrink-0">
              <form onSubmit={handleFormSubmit} className="flex gap-2 items-center">
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Ask about European customers, order status, or contact details..."
                  className="flex-1 bg-[#091124] border-slate-800 text-slate-100 text-xs placeholder:text-slate-500 focus-visible:ring-blue-500/40 rounded-xl h-10 px-3.5"
                  disabled={isProcessing}
                />
                <Button 
                  type="submit" 
                  disabled={isProcessing || !inputText.trim()} 
                  className="bg-blue-600 hover:bg-blue-500 text-white rounded-xl h-10 w-10 p-0 flex items-center justify-center shrink-0 shadow-sm transition-colors disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>

          </div>

          {/* Minimal 3-Step Collapsible A2A Activity Panel */}
          {isActivityOpen && (
            <div className="w-[320px] lg:w-[350px] shrink-0 bg-[#091124] border border-slate-800/90 rounded-2xl flex flex-col overflow-hidden shadow-sm transition-all">
              
              {/* Activity Header */}
              <div className="px-4 py-3 border-b border-slate-800/80 bg-[#070e20] flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <h3 className="font-semibold text-slate-200 text-xs tracking-tight">A2A Communication Activity</h3>
                </div>
                <div className="flex items-center gap-1">
                  <Badge variant="outline" className="bg-blue-950/60 border-blue-800 text-blue-300 text-[10px] px-1.5 py-0.2 font-mono">
                    3 Hops
                  </Badge>
                  <button 
                    onClick={() => setIsActivityOpen(false)}
                    className="text-slate-500 hover:text-slate-300 p-1 transition-colors"
                    title="Close Panel"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Minimal 3 Connected Cards */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 font-sans">
                <div className="text-[11px] text-slate-400 leading-relaxed mb-3">
                  Every query follows an isolated 3-step cross-border lifecycle:
                </div>

                {activitySteps.map((step, idx) => {
                  const isBlue = step.color === 'blue';
                  const isPurple = step.color === 'purple';
                  const isEmerald = step.color === 'emerald';

                  return (
                    <div 
                      key={idx} 
                      className={`p-3.5 rounded-xl border transition-all ${
                        isBlue ? 'bg-[#070d1d] border-blue-900/50' :
                        isPurple ? 'bg-[#0b0a1d] border-purple-900/50' :
                        'bg-[#06121a] border-emerald-900/50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            isBlue ? 'bg-blue-400' :
                            isPurple ? 'bg-purple-400' :
                            'bg-emerald-400'
                          }`} />
                          <span className="text-xs font-semibold text-slate-200">
                            {step.title}
                          </span>
                        </div>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                          isBlue ? 'bg-blue-950 text-blue-300 border-blue-800' :
                          isPurple ? 'bg-purple-950 text-purple-300 border-purple-800' :
                          'bg-emerald-950 text-emerald-300 border-emerald-800'
                        }`}>
                          {step.badge}
                        </span>
                      </div>

                      <div className="text-[11px] font-medium text-slate-400 mb-1">
                        {step.node}
                      </div>

                      <p className="text-[11px] text-slate-500 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  );
                })}

                {/* Status Notice */}
                <div className="mt-4 p-3 bg-[#060b18] border border-slate-800/80 rounded-xl text-[11px] text-slate-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
                  <span>Cross-border A2A link verified &bull; Standard telemetry</span>
                </div>
              </div>

            </div>
          )}

        </div>

      </main>

    </div>
  );
}

// Format markdown text and clean Shadcn-style tables
function FormattedMessage({ text }: { text: string }) {
  if (!text) return null;

  // Check if text contains a markdown table
  if (text.includes('|') && text.includes('\n|')) {
    const lines = text.split('\n');
    const introLines: string[] = [];
    const tableLines: string[] = [];
    const outroLines: string[] = [];
    let state: 'intro' | 'table' | 'outro' = 'intro';

    for (const line of lines) {
      if (line.trim().startsWith('|')) {
        state = 'table';
        tableLines.push(line.trim());
      } else if (state === 'table') {
        state = 'outro';
        outroLines.push(line);
      } else if (state === 'intro') {
        introLines.push(line);
      } else {
        outroLines.push(line);
      }
    }

    if (tableLines.length >= 2) {
      const headerCols = tableLines[0].split('|').slice(1, -1).map(c => c.trim());
      // Skip line index 1 (table divider like |---|---|)
      const dataRows = tableLines.slice(2).map(row => 
        row.split('|').slice(1, -1).map(c => c.trim())
      );

      return (
        <div className="space-y-3">
          {introLines.length > 0 && (
            <p className="text-slate-200 text-sm leading-relaxed">{introLines.join('\n')}</p>
          )}
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#080e20] shadow-sm max-h-80 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300 divide-y divide-slate-800">
              <thead className="bg-[#0b142c] text-[11px] font-semibold text-slate-400 uppercase tracking-wider sticky top-0">
                <tr>
                  {headerCols.map((col, idx) => (
                    <th key={idx} className="px-3.5 py-2.5">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {dataRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-800/30 transition-colors">
                    {row.map((cell, cIdx) => {
                      const cellLower = cell.toLowerCase();
                      const isDelivered = cellLower === 'delivered';
                      const isShipped = cellLower === 'shipped';
                      const isProcessing = cellLower === 'processing';
                      const isCancelled = cellLower === 'cancelled' || cellLower === 'canceled';

                      if (isDelivered || isShipped || isProcessing || isCancelled) {
                        return (
                          <td key={cIdx} className="px-3.5 py-2">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
                              isDelivered ? 'bg-emerald-950/70 text-emerald-300 border-emerald-800' :
                              isShipped ? 'bg-blue-950/70 text-blue-300 border-blue-800' :
                              isProcessing ? 'bg-amber-950/70 text-amber-300 border-amber-800' :
                              'bg-rose-950/40 text-rose-300 border-rose-900/50'
                            }`}>
                              {cell}
                            </span>
                          </td>
                        );
                      }
                      return (
                        <td key={cIdx} className="px-3.5 py-2 whitespace-nowrap text-slate-200">
                          {cell}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {outroLines.length > 0 && (
            <p className="text-slate-300 text-sm leading-relaxed">{outroLines.join('\n')}</p>
          )}
        </div>
      );
    }
  }

  // Otherwise render formatted text (bold, bullet points, clean spacing)
  const rawLines = text.split('\n');
  const items: { type: 'bullet' | 'paragraph'; text: string }[] = [];
  
  for (let i = 0; i < rawLines.length; i++) {
    const trimmed = rawLines[i].trim();
    if (!trimmed) continue;
    
    if (trimmed === '•' || trimmed === '-') {
      // Detached bullet: merge with next non-empty line
      if (i + 1 < rawLines.length && rawLines[i + 1].trim()) {
        items.push({ type: 'bullet', text: rawLines[i + 1].trim() });
        i++;
      }
    } else if (trimmed.startsWith('•') || trimmed.startsWith('- ')) {
      items.push({ type: 'bullet', text: trimmed.replace(/^[•\-]\s*/, '') });
    } else {
      items.push({ type: 'paragraph', text: trimmed });
    }
  }

  return (
    <div className="space-y-2 text-sm text-slate-200 leading-relaxed">
      {items.map((item, idx) => {
        if (item.type === 'bullet') {
          return (
            <div key={idx} className="flex items-start gap-2.5 pl-1 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 shrink-0 shadow-[0_0_6px_rgba(59,130,246,0.6)]" />
              <span className="text-slate-200 leading-snug">{renderBold(item.text)}</span>
            </div>
          );
        }
        return <p key={idx} className="leading-relaxed">{renderBold(item.text)}</p>;
      })}
    </div>
  );
}

function renderBold(str: string) {
  const parts = str.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={idx} className="font-semibold text-slate-100">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}
