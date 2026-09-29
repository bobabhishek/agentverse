import React, { useState, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight, ChevronDown, Search } from 'lucide-react';
import { FemaTestCase } from '../types';

interface TestCaseSelectorProps {
  testCases: FemaTestCase[];
  selectedTestCase: FemaTestCase;
  onSelectTestCase: (testCase: FemaTestCase) => void;
  filterMode: 'all' | 'failures' | 'valid';
  setFilterMode: (mode: 'all' | 'failures' | 'valid') => void;
}

export const TestCaseSelector: React.FC<TestCaseSelectorProps> = ({
  testCases,
  selectedTestCase,
  onSelectTestCase,
  filterMode,
  setFilterMode
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter lists
  const failureCases = testCases.filter((tc) => tc.policy_violations.length > 0);
  const validCases = testCases.filter((tc) => tc.policy_violations.length === 0);

  const displayedList =
    filterMode === 'failures'
      ? failureCases
      : filterMode === 'valid'
      ? validCases
      : testCases;

  const filteredDisplayList = displayedList.filter((tc) => {
    const q = searchQuery.toLowerCase();
    return (
      tc.person_id.toLowerCase().includes(q) ||
      tc.name.toLowerCase().includes(q) ||
      tc.purpose.toLowerCase().includes(q) ||
      tc.amount.toString().includes(q)
    );
  });

  const currentIndex = displayedList.findIndex((tc) => tc.person_id === selectedTestCase.person_id);

  const handlePrev = () => {
    if (displayedList.length === 0) return;
    if (currentIndex <= 0) {
      onSelectTestCase(displayedList[displayedList.length - 1]);
    } else {
      onSelectTestCase(displayedList[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    if (displayedList.length === 0) return;
    if (currentIndex < 0 || currentIndex >= displayedList.length - 1) {
      onSelectTestCase(displayedList[0]);
    } else {
      onSelectTestCase(displayedList[currentIndex + 1]);
    }
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const failureCount = selectedTestCase.policy_violations.length;

  return (
    <div className="rounded-2xl border border-slate-800/90 bg-[#060b18] p-4 sm:p-5 shadow-sm" ref={dropdownRef}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3.5">
        <span className="text-[11px] font-mono tracking-[0.18em] text-slate-300 uppercase font-semibold">
          TEST CASE
        </span>
        <span
          className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono tracking-wider font-semibold ${
            failureCount > 0
              ? 'bg-amber-500/10 border border-amber-500/30 text-amber-300'
              : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
          }`}
        >
          {failureCount > 0 ? `${failureCount} policy failure(s)` : '0 policy failure(s)'}
        </span>
      </div>

      {/* Filter Tabs Row */}
      <div className="flex items-center gap-2 mb-3 font-mono text-xs">
        <button
          onClick={() => {
            setFilterMode('all');
            setSearchQuery('');
          }}
          className={`px-3 py-1 rounded-full transition-colors cursor-pointer border ${
            filterMode === 'all'
              ? 'bg-[#121c38] text-blue-300 border-blue-500/40 shadow-sm'
              : 'bg-[#091124] text-slate-400 border-slate-800 hover:text-slate-200'
          }`}
        >
          All {testCases.length}
        </button>

        <button
          onClick={() => {
            setFilterMode('failures');
            setSearchQuery('');
            if (failureCases.length > 0 && selectedTestCase.policy_violations.length === 0) {
              onSelectTestCase(failureCases[0]);
            }
          }}
          className={`px-3 py-1 rounded-full transition-colors cursor-pointer border ${
            filterMode === 'failures'
              ? 'bg-[#121c38] text-blue-300 border-blue-500/40 shadow-sm'
              : 'bg-[#091124] text-slate-400 border-slate-800 hover:text-slate-200'
          }`}
        >
          Policy failures {failureCases.length}
        </button>

        <button
          onClick={() => {
            setFilterMode('valid');
            setSearchQuery('');
            if (validCases.length > 0 && selectedTestCase.policy_violations.length > 0) {
              onSelectTestCase(validCases[0]);
            }
          }}
          className={`px-3 py-1 rounded-full transition-colors cursor-pointer border ${
            filterMode === 'valid'
              ? 'bg-[#121c38] text-blue-300 border-blue-500/40 shadow-sm'
              : 'bg-[#091124] text-slate-400 border-slate-800 hover:text-slate-200'
          }`}
        >
          Valid-looking {validCases.length}
        </button>
      </div>

      {/* Selector Row */}
      <div className="relative flex items-center gap-1.5">
        <button
          onClick={handlePrev}
          title="Previous test case"
          className="w-8 h-9 rounded-xl bg-[#091124] border border-slate-800 hover:bg-[#0f1b38] hover:border-slate-700 text-slate-300 flex items-center justify-center transition-colors cursor-pointer shrink-0"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex-1 h-9 px-3 rounded-xl bg-[#091124] border border-slate-800 hover:border-blue-500/40 text-left flex items-center justify-between text-xs font-mono transition-colors cursor-pointer truncate"
        >
          <span className="truncate text-slate-200">
            <strong className="text-white">
              {selectedTestCase.person_id.replace('TEST-', '')}
            </strong>
            {' · '}${selectedTestCase.amount} {selectedTestCase.currency}
            {' · '}{selectedTestCase.purpose}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1.5 shrink-0" />
        </button>

        <button
          onClick={handleNext}
          title="Next test case"
          className="w-8 h-9 rounded-xl bg-[#091124] border border-slate-800 hover:bg-[#0f1b38] hover:border-slate-700 text-slate-300 flex items-center justify-center transition-colors cursor-pointer shrink-0"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Dropdown Menu */}
        {dropdownOpen && (
          <div className="absolute top-11 left-0 right-0 z-50 bg-[#091124] border border-slate-800 rounded-2xl shadow-2xl p-2 max-h-72 flex flex-col font-mono text-xs">
            {/* Search Input */}
            <div className="relative mb-2 shrink-0">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search test case or purpose..."
                className="w-full bg-[#060b18] border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/60"
                autoFocus
              />
            </div>

            {/* List */}
            <div className="overflow-y-auto space-y-1 flex-1 pr-1">
              {filteredDisplayList.length === 0 ? (
                <div className="py-4 text-center text-slate-400 text-xs">
                  No matching test cases found.
                </div>
              ) : (
                filteredDisplayList.map((tc) => {
                  const isSelected = tc.person_id === selectedTestCase.person_id;
                  const hasViolations = tc.policy_violations.length > 0;
                  return (
                    <div
                      key={tc.person_id}
                      onClick={() => {
                        onSelectTestCase(tc);
                        setDropdownOpen(false);
                      }}
                      className={`p-2 rounded-xl flex items-center justify-between cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-[#121c38] border border-blue-500/40 text-blue-200'
                          : 'hover:bg-slate-800/40 text-slate-300'
                      }`}
                    >
                      <div className="truncate">
                        <span className="font-semibold text-white">
                          {tc.person_id.replace('TEST-', '')}
                        </span>
                        {' · '}${tc.amount} {tc.currency} · {tc.purpose}
                      </div>
                      <span
                        className={`text-[10px] px-1.5 py-0.2 rounded font-mono ml-2 shrink-0 ${
                          hasViolations
                            ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30'
                            : 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                        }`}
                      >
                        {hasViolations ? `${tc.policy_violations.length} fail` : 'valid'}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
