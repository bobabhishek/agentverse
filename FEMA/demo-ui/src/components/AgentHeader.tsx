import React from 'react';
import { Bot } from 'lucide-react';

interface AgentHeaderProps {
  onNewChat?: () => void;
}

export const AgentHeader: React.FC<AgentHeaderProps> = () => {
  return (
    <div className="shrink-0 px-4 sm:px-6 py-2.5 border-b border-slate-800/70 bg-[#080d1c]/80 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 select-none">
      {/* Left: Icon and Title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
          <Bot className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-slate-100 tracking-tight leading-none mb-0.5">
            FEMA Payment Agent
          </h1>
          <p className="text-[11px] text-slate-400 font-mono">
            Cross-border payment requests · single agent
          </p>
        </div>
      </div>

      {/* Badges Row */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Status: Active</span>
        </div>
        <div className="px-2.5 py-1 rounded-full bg-blue-950/50 border border-blue-600/40 text-blue-300 text-[11px] font-mono">
          Guardrails: Active
        </div>
        <div className="px-2.5 py-1 rounded-full bg-amber-950/40 border border-amber-500/30 text-amber-300 text-[11px] font-mono">
          Environment: Simulation
        </div>
      </div>
    </div>
  );
};
