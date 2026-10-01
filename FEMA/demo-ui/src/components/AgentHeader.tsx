import React from 'react';
import { Bot } from 'lucide-react';

interface AgentHeaderProps {
  onNewChat?: () => void;
  senderCountry: 'India' | 'United States';
  onSelectSenderCountry: (country: 'India' | 'United States') => void;
  activeSenderName?: string;
  balances?: { INR: number; USD: number };
}

export const AgentHeader: React.FC<AgentHeaderProps> = ({
  senderCountry,
  onSelectSenderCountry,
  activeSenderName
}) => {
  return (
    <div className="shrink-0 px-4 sm:px-6 py-2.5 border-b border-white/[0.08] bg-black/40 backdrop-blur-md flex flex-col lg:flex-row lg:items-center justify-between gap-3 select-none">
      {/* Left: Icon and Title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-sm shrink-0">
          <Bot className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-slate-100 tracking-tight leading-none">
              FEMA Payment Agent
            </h1>
            {activeSenderName && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/[0.06] border border-white/[0.1] text-slate-300">
                Sender: <strong className="text-white">{activeSenderName}</strong>
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">
            Single autonomous rogue compliance agent · SQLite persistent ledger
          </p>
        </div>
      </div>

      {/* Center: SENDER ACCOUNT COUNTRY TOGGLE */}
      <div className="flex items-center self-start lg:self-center gap-2">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider hidden sm:inline">
          Sender Account:
        </span>
        <div className="flex items-center gap-1.5 p-1 bg-black/60 border border-white/[0.12] rounded-xl shadow-inner">
          <button
            type="button"
            onClick={() => onSelectSenderCountry('India')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-bold tracking-wide transition-all cursor-pointer ${
              senderCountry === 'India'
                ? 'bg-gradient-to-r from-orange-600/30 to-amber-600/20 text-orange-200 border border-orange-500/50 shadow-md shadow-orange-500/10 scale-[1.02]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] border border-transparent'
            }`}
          >
            <span className="text-sm leading-none">🇮🇳</span>
            <span>INDIA ACCOUNT</span>
          </button>
          <button
            type="button"
            onClick={() => onSelectSenderCountry('United States')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-bold tracking-wide transition-all cursor-pointer ${
              senderCountry === 'United States'
                ? 'bg-gradient-to-r from-blue-600/30 to-indigo-600/20 text-blue-200 border border-blue-500/50 shadow-md shadow-blue-500/10 scale-[1.02]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] border border-transparent'
            }`}
          >
            <span className="text-sm leading-none">🇺🇸</span>
            <span>USA ACCOUNT</span>
          </button>
        </div>
      </div>

      {/* Right: Badges Row */}
      <div className="flex flex-wrap items-center gap-1.5">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-emerald-950/50 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono shadow-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Status: Active</span>
        </div>
        <div className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-blue-950/50 border border-blue-500/30 text-blue-300 text-[11px] font-mono shadow-xs">
          Guardrails: Active
        </div>
        <div className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-amber-950/40 border border-amber-500/30 text-amber-300 text-[11px] font-mono shadow-xs">
          Simulation
        </div>
      </div>
    </div>
  );
};
export default AgentHeader;
