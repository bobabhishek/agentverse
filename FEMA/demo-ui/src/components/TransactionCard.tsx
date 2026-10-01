import React from 'react';
import { ArrowRight, ArrowLeftRight } from 'lucide-react';
import { FemaTestCase } from '../types';

interface TransactionCardProps {
  testCase: FemaTestCase;
  isReverseRoute: boolean;
  onToggleRoute: () => void;
  balances?: { INR: number; USD: number };
}

export const TransactionCard: React.FC<TransactionCardProps> = ({
  testCase,
  isReverseRoute,
  onToggleRoute,
  balances = { INR: 100000, USD: 10000 }
}) => {
  const fromCountry = isReverseRoute ? testCase.destination_country : testCase.source_country;
  const toCountry = isReverseRoute ? testCase.source_country : testCase.destination_country;

  const senderName = isReverseRoute ? testCase.recipient_name : testCase.name;
  const recipientName = isReverseRoute ? testCase.name : testCase.recipient_name;

  const currentBal = isReverseRoute ? balances.USD : balances.INR;
  const currSym = isReverseRoute ? '$' : '₹';
  const currCode = isReverseRoute ? 'USD' : 'INR';

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-black/45 backdrop-blur-md p-4 sm:p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3.5">
        <span className="text-[11px] font-mono tracking-[0.18em] text-slate-300 uppercase font-semibold">
          TRANSACTION · {testCase.transaction_id.replace('-', ' ')}
        </span>
        <button
          type="button"
          onClick={onToggleRoute}
          title="Swap remittance direction between India and US"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono uppercase tracking-wider font-semibold bg-white/[0.05] hover:bg-white/[0.10] border border-white/[0.08] hover:border-blue-500/30 text-blue-300 transition-colors cursor-pointer backdrop-blur-xs"
        >
          <ArrowLeftRight className="w-3 h-3 text-blue-400" />
          <span>{isReverseRoute ? 'US → India' : 'India → US'}</span>
        </button>
      </div>

      {/* From / To Route Box */}
      <div className="grid grid-cols-11 items-center gap-2 p-3.5 rounded-xl bg-black/40 backdrop-blur-xs border border-white/[0.08] mb-4">
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
      <div className="mb-3.5 px-3 py-1.5 rounded-xl bg-black/50 backdrop-blur-xs border border-blue-500/40 flex items-center justify-between text-[11px] font-mono">
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

        {/* Dynamic Available Balance */}
        <div className="col-span-2 pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-wider text-slate-400">
            AVAILABLE SENDER BALANCE
          </span>
          <span className="text-xs font-bold text-emerald-400">
            {currSym}{currentBal.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} {currCode}
          </span>
        </div>
      </div>
    </div>
  );
};
