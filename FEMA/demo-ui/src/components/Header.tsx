import React from 'react';
import { ShieldAlert, SlidersHorizontal, PanelLeft, PanelLeftClose } from 'lucide-react';
import { FemaTestCase } from '../types';

interface HeaderProps {
  activeTab: 'agent' | 'documentation';
  setActiveTab: (tab: 'agent' | 'documentation') => void;
  selectedTestCase?: FemaTestCase;
  onOpenDrawer?: () => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  selectedTestCase,
  onOpenDrawer,
  isSidebarOpen,
  onToggleSidebar
}) => {
  const failureCount = selectedTestCase?.policy_violations.length ?? 0;

  return (
    <header className="border-b border-slate-800/80 bg-[#080e1f]/90 backdrop-blur-md sticky top-0 z-40 px-3 sm:px-6 py-2.5">
      <div className="max-w-[1720px] mx-auto flex items-center justify-between">
        {/* Left: Sidebar Toggle + Title */}
        <div className="flex items-center gap-3">
          {onToggleSidebar && activeTab === 'agent' && (
            <button
              onClick={onToggleSidebar}
              title={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              className="p-1.5 rounded-lg bg-[#0a1126] hover:bg-blue-950/40 border border-slate-800 hover:border-blue-500/40 text-slate-400 hover:text-blue-300 transition-colors cursor-pointer"
            >
              {isSidebarOpen ? (
                <PanelLeftClose className="w-4 h-4 text-blue-400" />
              ) : (
                <PanelLeft className="w-4 h-4 text-slate-400" />
              )}
            </button>
          )}

          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)]"></span>
            </span>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-slate-100 tracking-tight">
                Guardrail Test Bench
              </span>
              <span className="text-[10px] tracking-wider uppercase font-mono text-blue-400/90 bg-blue-950/60 border border-blue-800/50 px-1.5 py-0.2 rounded">
                FEMA AGENT
              </span>
            </div>
          </div>
        </div>

        {/* Center: Tabs */}
        <div className="flex items-center bg-[#070d1d] p-1 rounded-xl border border-slate-800">
          <button
            id="nav-agent-tab"
            onClick={() => setActiveTab('agent')}
            className={`px-4 sm:px-5 py-1 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
              activeTab === 'agent'
                ? 'bg-[#121c38] text-blue-300 border border-blue-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            Agent
          </button>
          <button
            id="nav-docs-tab"
            onClick={() => setActiveTab('documentation')}
            className={`px-4 sm:px-5 py-1 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
              activeTab === 'documentation'
                ? 'bg-[#121c38] text-blue-300 border border-blue-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            Documentation
          </button>
        </div>

        {/* Right: Simulation Pill & Drawer Toggle Button */}
        <div className="flex items-center gap-2">
          {onOpenDrawer && activeTab === 'agent' && (
            <button
              onClick={onOpenDrawer}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0a1126] hover:bg-blue-950/40 border border-slate-800 hover:border-blue-500/40 text-xs font-mono text-slate-300 hover:text-blue-300 transition-colors cursor-pointer shadow-sm"
            >
              <SlidersHorizontal className="w-3.5 h-3.5 text-blue-400" />
              <span className="hidden md:inline">Test Case & Policy</span>
              {selectedTestCase && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                    failureCount > 0
                      ? 'bg-amber-950/70 text-amber-300 border border-amber-500/30'
                      : 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/30'
                  }`}
                >
                  {failureCount > 0 ? `${failureCount} fail` : 'valid'}
                </span>
              )}
            </button>
          )}

          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-amber-950/40 border border-amber-500/30 text-amber-300 text-[11px] font-mono font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span className="hidden lg:inline">SIMULATION ONLY • </span>
            <span>NO REAL FUNDS</span>
          </div>
        </div>
      </div>
    </header>
  );
};
