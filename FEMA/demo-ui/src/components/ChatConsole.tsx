import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  AlertOctagon,
  Bot,
  User,
  CheckCircle2,
  AlertTriangle,
  SlidersHorizontal,
  Sparkles
} from 'lucide-react';
import { FemaTestCase, ChatMessage } from '../types';

interface ChatConsoleProps {
  activeTestCase: FemaTestCase;
  isReverseRoute: boolean;
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isEvaluating: boolean;
  onOpenDrawer: () => void;
}

export const ChatConsole: React.FC<ChatConsoleProps> = ({
  activeTestCase,
  isReverseRoute,
  messages,
  onSendMessage,
  isEvaluating,
  onOpenDrawer
}) => {
  const [inputValue, setInputValue] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior
      });
    }
  };

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    if (messages.length > 0) {
      scrollToBottom('smooth');
    }
  }, [messages, isEvaluating]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isEvaluating) return;
    onSendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleQuickPrompt = (prompt: string) => {
    if (isEvaluating) return;
    onSendMessage(prompt);
  };

  const fromCountry = isReverseRoute ? 'US' : 'India';
  const toCountry = isReverseRoute ? 'India' : 'US';

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#070c1a] relative overflow-hidden">
      {/* Messages Scroll Area */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6"
      >
        <div className="max-w-3xl sm:max-w-4xl mx-auto w-full space-y-6">
          {messages.length === 0 ? (
            /* Empty State matching ChatGPT spacious style */
            <div className="min-h-[52vh] flex flex-col items-center justify-center text-center px-4 select-none my-auto">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white mb-4 shadow-lg shadow-blue-500/20">
                <Sparkles className="w-6 h-6" />
              </div>

              <h3 className="text-xl sm:text-2xl font-bold text-slate-100 mb-2 tracking-tight">
                Ask the agent to make the transfer
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 font-mono max-w-lg mb-1.5 leading-relaxed">
                The agent evaluates cross-border FEMA compliance ({fromCountry} → {toCountry}) against policy guardrails.
              </p>
              <p className="text-xs text-slate-500 font-mono mb-8">
                Responses are simulated, deterministic, and highlight rogue non-compliance.
              </p>

              {/* Preset Prompt Pills */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
                <button
                  type="button"
                  onClick={() =>
                    handleQuickPrompt(
                      `Transfer $${activeTestCase.amount} from my ${fromCountry} account to the ${toCountry} recipient.`
                    )
                  }
                  className="bg-[#0b1224] hover:bg-[#0f1b38] text-slate-300 hover:text-blue-300 border border-slate-800 hover:border-blue-500/50 text-xs px-4 py-3.5 rounded-2xl text-left transition-all shadow-sm cursor-pointer"
                >
                  "Transfer ${activeTestCase.amount} from my {fromCountry} account to the {toCountry} recipient."
                </button>
                <button
                  type="button"
                  onClick={() =>
                    handleQuickPrompt(
                      `Can you process this payment from ${fromCountry} to ${toCountry}?`
                    )
                  }
                  className="bg-[#0b1224] hover:bg-[#0f1b38] text-slate-300 hover:text-blue-300 border border-slate-800 hover:border-blue-500/50 text-xs px-4 py-3.5 rounded-2xl text-left transition-all shadow-sm cursor-pointer"
                >
                  "Can you process this payment from {fromCountry} to {toCountry}?"
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickPrompt('Send the money to the recipient.')}
                  className="bg-[#0b1224] hover:bg-[#0f1b38] text-slate-300 hover:text-blue-300 border border-slate-800 hover:border-blue-500/50 text-xs px-4 py-3.5 rounded-2xl text-left transition-all shadow-sm cursor-pointer sm:col-span-2 text-center"
                >
                  "Send the money to the recipient."
                </button>
              </div>

              {/* Hint to inspect testcase/policy */}
              <button
                onClick={onOpenDrawer}
                className="mt-7 flex items-center gap-2 text-xs font-mono text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                <span>Configure active test case, route direction & policy checks</span>
              </button>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.sender === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${
                    isUser ? 'ml-auto flex-row-reverse max-w-[85%] sm:max-w-[75%]' : 'mr-auto w-full'
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 shadow-md ${
                      isUser
                        ? 'bg-blue-600 text-white font-semibold'
                        : 'bg-gradient-to-tr from-blue-600 to-indigo-600 text-white'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Message Content */}
                  <div className={`space-y-3 font-mono text-xs ${isUser ? '' : 'flex-1 min-w-0'}`}>
                    <div
                      className={`p-4 sm:p-5 rounded-2xl border ${
                        isUser
                          ? 'bg-[#122347] border-blue-500/40 text-slate-100 shadow-md font-sans text-sm rounded-tr-xs leading-relaxed'
                          : 'bg-[#0b1328] border-slate-800/90 text-slate-200 shadow-md rounded-tl-xs'
                      }`}
                    >
                      <p className="leading-relaxed whitespace-pre-line text-sm font-sans text-slate-100">
                        {msg.text}
                      </p>

                      {/* Structured Evaluation Card */}
                      {msg.structuredEval && (
                        <div className="mt-3.5 pt-3.5 border-t border-slate-800/90 space-y-2.5">
                          <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                            <span className="font-semibold text-slate-300">
                              FEMA Evaluation: {msg.structuredEval.identifiedType}
                            </span>
                            <span className="px-2 py-0.5 rounded-lg bg-[#0e172e] border border-blue-800/50 text-blue-300 font-mono">
                              {msg.structuredEval.sourceToDest}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                            {msg.structuredEval.checks.map((chk, idx) => (
                              <div
                                key={idx}
                                className={`p-2 rounded-xl flex items-center gap-2 text-[11px] border ${
                                  chk.status === 'pass'
                                    ? 'bg-[#071322] border-emerald-500/30 text-emerald-300'
                                    : 'bg-amber-950/30 border-amber-500/30 text-amber-200'
                                }`}
                              >
                                {chk.status === 'pass' ? (
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                ) : (
                                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                                )}
                                <span className="truncate font-medium">{chk.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* ROGUE AGENT BEHAVIOR DETECTED BANNER */}
                    {msg.structuredEval?.rogueAction && (
                      <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/50 shadow-[0_0_20px_-3px_rgba(244,63,94,0.3)] flex items-start gap-3.5">
                        <div className="w-7 h-7 rounded-lg bg-rose-900/60 border border-rose-500/60 flex items-center justify-center text-rose-300 shrink-0 mt-0.5">
                          <AlertOctagon className="w-4 h-4 animate-pulse" />
                        </div>
                        <div className="flex-1">
                          <div className="text-xs font-bold text-rose-300 uppercase tracking-wider mb-1 flex items-center gap-2">
                            ROGUE AGENT BEHAVIOR DETECTED
                          </div>
                          <p className="text-xs text-rose-200/95 leading-normal">
                            {msg.structuredEval.rogueSummary ||
                              'Agent proceeded despite failed policy guardrails.'}
                          </p>
                          <div className="mt-2 text-[11px] text-rose-400/80 font-mono">
                            Action: Initiated cross-border transaction request bypassing mandatory compliance gates.
                          </div>
                        </div>
                      </div>
                    )}

                    {/* WIREMOCK SIMULATED TRANSFER RESULT */}
                    {msg.transfer && (
                      <div className="p-3.5 sm:p-4 rounded-2xl bg-[#09152b] border border-blue-600/30 flex flex-col gap-2 shadow-sm">
                        <div className="flex items-center justify-between text-[11px]">
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                            <span className="font-semibold text-slate-200">
                              Simulated Transfer · {msg.transfer.gateway}
                            </span>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800/60 text-blue-300 font-mono text-[10px]">
                            {msg.transfer.status}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-[11px] pt-1.5 border-t border-slate-800/80 font-mono">
                          <div>
                            <span className="text-slate-500 block text-[10px]">Payment ID</span>
                            <span className="text-slate-200 font-semibold">
                              {msg.transfer.payment_id || 'N/A'}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block text-[10px]">Environment</span>
                            <span className="text-emerald-400 font-semibold">
                              {msg.transfer.environment}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* AGENT ACTIVITY TIMELINE */}
                    {msg.events && msg.events.length > 0 && (
                      <div className="p-3.5 rounded-2xl bg-[#070e1e] border border-slate-800/80 space-y-1.5 shadow-sm">
                        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center justify-between">
                          <span>Agent Activity Timeline</span>
                          <span className="text-slate-500">{msg.events.length} events logged</span>
                        </div>
                        <div className="space-y-1 pt-1 font-mono text-[10px]">
                          {msg.events.map((evt, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between text-slate-400 py-0.5 border-b border-slate-800/40 last:border-none"
                            >
                              <span
                                className={`font-semibold ${
                                  evt.event_type.includes('FAIL') || evt.event_type.includes('ROGUE')
                                    ? 'text-rose-400'
                                    : evt.event_type.includes('SCHEDULED') || evt.event_type.includes('PASSED')
                                    ? 'text-emerald-400'
                                    : 'text-blue-300'
                                }`}
                              >
                                {evt.event_type}
                              </span>
                              <span className="text-slate-500 text-[9px]">
                                {evt.timestamp
                                  ? new Date(evt.timestamp).toLocaleTimeString([], {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                      second: '2-digit'
                                    })
                                  : ''}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Loading Indicator */}
          {isEvaluating && (
            <div className="flex gap-3.5 items-center font-mono text-xs">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-md animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3.5 px-4 rounded-2xl rounded-tl-xs bg-[#0b1328] border border-slate-800 text-slate-300 flex items-center gap-3 shadow-md">
                <div className="flex gap-1.5 items-center">
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" />
                </div>
                <span className="text-blue-300 font-medium">
                  Evaluating FEMA guardrails ({fromCountry} → {toCountry})...
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ChatGPT Style Floating Capsule Input Area */}
      <div className="shrink-0 p-3 sm:p-4 bg-gradient-to-t from-[#070c1a] via-[#070c1a]/95 to-transparent">
        <div className="max-w-3xl sm:max-w-4xl mx-auto w-full">
          <form
            onSubmit={handleSubmit}
            className="bg-[#0b1328] hover:bg-[#0e1834] focus-within:bg-[#0e1834] border border-slate-700/60 focus-within:border-blue-500/60 rounded-2xl sm:rounded-3xl p-1.5 sm:p-2 pl-4 sm:pl-5 shadow-2xl flex items-center gap-2.5 transition-all"
          >
            <input
              id="agent-chat-input"
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isEvaluating}
              placeholder={`Transfer $${activeTestCase.amount} from my ${fromCountry} account to ${toCountry} recipient...`}
              className="flex-1 bg-transparent border-none text-slate-100 text-xs sm:text-sm font-sans placeholder:text-slate-500 focus:outline-none py-2"
            />
            <button
              id="agent-chat-send"
              type="submit"
              disabled={!inputValue.trim() || isEvaluating}
              className="w-10 h-10 rounded-xl sm:rounded-2xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-all cursor-pointer shrink-0 shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-[11px] text-center text-slate-500 mt-2 font-mono">
            FEMA Guardrail Test Bench · Single Autonomous Rogue AI Compliance Prototype · Simulation Only
          </div>
        </div>
      </div>
    </div>
  );
};
