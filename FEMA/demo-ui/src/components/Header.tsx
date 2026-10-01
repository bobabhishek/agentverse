import React from 'react';
import { ShieldAlert, SlidersHorizontal, PanelLeft, PanelLeftClose } from 'lucide-react';
import { FemaTestCase } from '../types';

interface HeaderProps {
  activeTab: 'agent' | 'database' | 'documentation';
  setActiveTab: (tab: 'agent' | 'database' | 'documentation') => void;
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
  const failureCount = selectedTestCase?.policy_violations?.length ?? 0;

  return (
    <header className="border-b border-white/[0.08] bg-black/40 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-6 py-2.5 w-full">
      <div className="w-full flex items-center justify-between relative">
        {/* Left: Sidebar Toggle + Title (Stably Anchored) */}
        <div className="flex items-center gap-3 shrink-0">
          {onToggleSidebar && (
            <button
              onClick={() => {
                if (activeTab !== 'agent') {
                  setActiveTab('agent');
                }
                onToggleSidebar();
              }}
              title={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              className={`p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.10] border border-white/[0.08] hover:border-blue-500/40 text-slate-400 hover:text-blue-300 transition-colors cursor-pointer backdrop-blur-xs ${
                activeTab !== 'agent' ? 'opacity-50 hover:opacity-100' : ''
              }`}
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
              <span className="text-[10px] tracking-wider uppercase font-mono text-blue-400/90 bg-blue-950/60 border border-blue-500/40 px-1.5 py-0.2 rounded">
                FEMA AGENT
              </span>
            </div>
          </div>
        </div>

        {/* Center: Tabs - Always Mathematically Centered */}
        <div className="hidden sm:flex items-center bg-black/50 p-1 rounded-xl border border-white/[0.08] shadow-sm absolute left-1/2 -translate-x-1/2 z-10 backdrop-blur-xs">
          <button
            id="nav-agent-tab"
            onClick={() => setActiveTab('agent')}
            className={`px-4 sm:px-5 py-1 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
              activeTab === 'agent'
                ? 'bg-white/[0.10] text-blue-300 border border-blue-500/40 shadow-xs font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
            }`}
          >
            Agent
          </button>
          <button
            id="nav-database-tab"
            onClick={() => setActiveTab('database')}
            className={`px-4 sm:px-5 py-1 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'database'
                ? 'bg-white/[0.10] text-emerald-300 border border-emerald-500/40 shadow-xs font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
            }`}
          >
            <span>Database</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          </button>
          <button
            id="nav-docs-tab"
            onClick={() => setActiveTab('documentation')}
            className={`px-4 sm:px-5 py-1 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
              activeTab === 'documentation'
                ? 'bg-white/[0.10] text-blue-300 border border-blue-500/40 shadow-xs font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
            }`}
          >
            Documentation
          </button>
        </div>

        {/* Right: Simulation Pill & Drawer Toggle Button (Stably Anchored) */}
        <div className="flex items-center gap-2 shrink-0">
          {onOpenDrawer && (
            <button
              onClick={onOpenDrawer}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.10] border border-white/[0.08] hover:border-blue-500/40 text-xs font-mono text-slate-300 hover:text-blue-300 transition-colors cursor-pointer shadow-sm backdrop-blur-xs"
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

          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-amber-950/40 border border-amber-500/30 text-amber-300 text-[11px] font-mono font-medium backdrop-blur-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span className="hidden lg:inline">SIMULATION ONLY • </span>
            <span>NO REAL FUNDS</span>
          </div>
        </div>
      </div>
    </header>
  );
};

