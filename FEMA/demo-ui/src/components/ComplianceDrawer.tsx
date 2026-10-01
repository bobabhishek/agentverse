import React, { useEffect } from 'react';
import { X, SlidersHorizontal } from 'lucide-react';
import { FemaTestCase } from '../types';
import { TestCaseSelector } from './TestCaseSelector';
import { TransactionCard } from './TransactionCard';
import { PolicyChecksCard } from './PolicyChecksCard';

interface ComplianceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  testCases: FemaTestCase[];
  selectedTestCase: FemaTestCase;
  onSelectTestCase: (tc: FemaTestCase) => void;
  filterMode: 'all' | 'failures' | 'valid';
  setFilterMode: (mode: 'all' | 'failures' | 'valid') => void;
  isReverseRoute: boolean;
  onToggleRoute: () => void;
  balances?: { INR: number; USD: number };
}

export const ComplianceDrawer: React.FC<ComplianceDrawerProps> = ({
  isOpen,
  onClose,
  testCases,
  selectedTestCase,
  onSelectTestCase,
  filterMode,
  setFilterMode,
  isReverseRoute,
  onToggleRoute,
  balances
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden font-sans">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
      />

      {/* Slide-over panel */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-6 sm:pl-10">
        <div className="w-screen max-w-[480px] bg-black/80 backdrop-blur-2xl border-l border-white/[0.12] shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out">
          {/* Drawer Header */}
          <div className="px-5 py-4 border-b border-white/[0.08] bg-black/40 backdrop-blur-md flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
                <SlidersHorizontal className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-100 font-mono tracking-tight">
                  TEST CASE & POLICY INSPECTOR
                </h2>
                <p className="text-[11px] text-slate-400 font-mono">
                  Configure test parameters & inspect guardrails
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              title="Close panel (Esc)"
              className="w-8 h-8 rounded-xl bg-white/[0.05] hover:bg-white/[0.10] border border-white/[0.08] text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer backdrop-blur-xs"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
            <TestCaseSelector
              testCases={testCases}
              selectedTestCase={selectedTestCase}
              onSelectTestCase={onSelectTestCase}
              filterMode={filterMode}
              setFilterMode={setFilterMode}
            />

            <TransactionCard
              testCase={selectedTestCase}
              isReverseRoute={isReverseRoute}
              onToggleRoute={onToggleRoute}
              balances={balances}
            />

            <PolicyChecksCard
              testCase={selectedTestCase}
              isReverseRoute={isReverseRoute}
            />
          </div>

          {/* Drawer Footer */}
          <div className="px-5 py-3 border-t border-white/[0.08] bg-black/40 backdrop-blur-md text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Status: <strong className="text-blue-300">{selectedTestCase.person_id}</strong> active</span>
            <button
              onClick={onClose}
              className="px-3.5 py-1 rounded-xl bg-white/[0.05] hover:bg-white/[0.10] text-blue-300 hover:text-blue-200 border border-blue-500/30 text-xs font-mono transition-colors cursor-pointer backdrop-blur-xs"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
