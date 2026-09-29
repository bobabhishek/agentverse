import React from 'react';
import { ArrowRight, ArrowLeftRight } from 'lucide-react';
import { FemaTestCase } from '../types';

interface TransactionCardProps {
  testCase: FemaTestCase;
  isReverseRoute: boolean;
  onToggleRoute: () => void;
}

export const TransactionCard: React.FC<TransactionCardProps> = ({
  testCase,
  isReverseRoute,
  onToggleRoute
}) => {
  const fromCountry = isReverseRoute ? testCase.destination_country : testCase.source_country;
  const toCountry = isReverseRoute ? testCase.source_country : testCase.destination_country;

  const senderName = isReverseRoute ? testCase.recipient_name : testCase.name;
  const recipientName = isReverseRoute ? testCase.name : testCase.recipient_name;

  return (
    <div className="rounded-2xl border border-slate-800/90 bg-[#060b18] p-4 sm:p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3.5">
        <span className="text-[11px] font-mono tracking-[0.18em] text-slate-300 uppercase font-semibold">
          TRANSACTION · {testCase.transaction_id.replace('-', ' ')}
        </span>
        <button
          type="button"
          onClick={onToggleRoute}
          title="Swap remittance direction between India and US"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono uppercase tracking-wider font-semibold bg-[#0d162e] hover:bg-blue-600/20 border border-blue-500/30 text-blue-300 transition-colors cursor-pointer"
        >
          <ArrowLeftRight className="w-3 h-3 text-blue-400" />
          <span>{isReverseRoute ? 'US → India' : 'India → US'}</span>
        </button>
      </div>

      {/* From / To Route Box */}
      <div className="grid grid-cols-11 items-center gap-2 p-3.5 rounded-xl bg-[#091124] border border-slate-800 mb-4">
        {/* From */}
        <div className="col-span-5 font-mono">
          <span className="text-[10px] tracking-wider uppercase text-slate-400 block mb-1">
            FROM
          </span>
          <div className="text-sm font-bold text-white tracking-tight">
            {fromCountry}
          </div>
        </div>

        {/* Arrow */}
        <div className="col-span-1 flex items-center justify-center text-blue-400">
          <ArrowRight className="w-4 h-4" />
        </div>

        {/* To */}
        <div className="col-span-5 font-mono">
          <span className="text-[10px] tracking-wider uppercase text-slate-400 block mb-1">
            TO
          </span>
          <div className="text-sm font-bold text-white tracking-tight">
            {toCountry}
          </div>
        </div>
      </div>

      {/* Remittance Type Badge */}
      <div className="mb-3.5 px-3 py-1.5 rounded-xl bg-[#0e172e] border border-blue-800/50 flex items-center justify-between text-[11px] font-mono">
        <span className="text-slate-400">FEMA Direction:</span>
        <span className="text-blue-300 font-semibold">
          {isReverseRoute ? 'Foreign Inward Remittance (FIRC / Inbound)' : 'Outward Remittance (LRS / Outbound)'}
        </span>
      </div>

      {/* Key Details Grid */}
      <div className="grid grid-cols-2 gap-3.5 font-mono text-xs">
        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
            AMOUNT
          </span>
          <span className="text-sm font-bold text-white">
            ${testCase.amount} {testCase.currency}
          </span>
        </div>

        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
            PURPOSE
          </span>
          <span className="text-sm font-medium text-slate-200 truncate block">
            {testCase.purpose}
          </span>
        </div>

        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
            SENDER
          </span>
          <span className="text-xs text-slate-300 truncate block">
            {senderName}
          </span>
        </div>

        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
            RECIPIENT
          </span>
          <span className="text-xs text-slate-300 truncate block">
            {recipientName}
          </span>
        </div>
      </div>
    </div>
  );
};
