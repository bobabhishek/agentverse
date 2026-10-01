import React, { useState, useEffect, useMemo } from 'react';
import {
  Database,
  RefreshCw,
  Search,
  ArrowRight,
  FileText,
  CheckCircle2,
  Users,
  UserCheck,
  Wallet,
  Clock,
  Sparkles,
  Download,
  Plus,
  X
} from 'lucide-react';
import {
  fetchDatabaseSummary,
  fetchDatabaseCustomers,
  fetchDatabaseRecipients,
  fetchDatabaseAccounts,
  fetchDatabaseTransactions,
  downloadAuditTrailPdf,
  createSyntheticPerson
} from '../services/api';

type DbTab = 'transactions' | 'customers' | 'recipients' | 'accounts';

const formatDateDDMMYYYY = (dateStr?: string | null): string => {
  if (!dateStr) return 'Just now';
  const match = dateStr.match(/^(\d{4})[-/](\d{2})[-/](\d{2})(.*)$/);
  if (match) {
    const [, yyyy, mm, dd, rest] = match;
    return `${dd}-${mm}-${yyyy}${rest}`;
  }
  const parsed = new Date(dateStr);
  if (!isNaN(parsed.getTime())) {
    const dd = String(parsed.getDate()).padStart(2, '0');
    const mm = String(parsed.getMonth() + 1).padStart(2, '0');
    const yyyy = parsed.getFullYear();
    const hh = String(parsed.getHours()).padStart(2, '0');
    const min = String(parsed.getMinutes()).padStart(2, '0');
    return `${dd}-${mm}-${yyyy} ${hh}:${min}`;
  }
  return dateStr;
};

const IndiaFlagIcon: React.FC = () => (
  <svg className="w-4 h-2.5 rounded-[2px] shrink-0 shadow-xs inline-block" viewBox="0 0 640 480" aria-label="India flag">
    <rect width="640" height="160" fill="#FF9933" />
    <rect y="160" width="640" height="160" fill="#FFFFFF" />
    <rect y="320" width="640" height="160" fill="#138808" />
    <circle cx="320" cy="240" r="48" fill="none" stroke="#000080" strokeWidth="6" />
    <circle cx="320" cy="240" r="10" fill="#000080" />
    {[...Array(24)].map((_, i) => (
      <line
        key={i}
        x1="320"
        y1="240"
        x2={320 + 48 * Math.cos((i * 15 * Math.PI) / 180)}
        y2={240 + 48 * Math.sin((i * 15 * Math.PI) / 180)}
        stroke="#000080"
        strokeWidth="2.5"
      />
    ))}
  </svg>
);

const UsaFlagIcon: React.FC = () => (
  <svg className="w-4 h-2.5 rounded-[2px] shrink-0 shadow-xs inline-block" viewBox="0 0 640 480" aria-label="US flag">
    <rect width="640" height="480" fill="#B22234" />
    <path
      d="M0,36.92h640M0,110.77h640M0,184.62h640M0,258.46h640M0,332.31h640M0,406.15h640"
      stroke="#FFFFFF"
      strokeWidth="36.92"
    />
    <rect width="256" height="258.46" fill="#3C3B6E" />
    <g fill="#FFFFFF">
      <circle cx="35" cy="30" r="8" />
      <circle cx="85" cy="30" r="8" />
      <circle cx="135" cy="30" r="8" />
      <circle cx="185" cy="30" r="8" />
      <circle cx="60" cy="65" r="8" />
      <circle cx="110" cy="65" r="8" />
      <circle cx="160" cy="65" r="8" />
      <circle cx="210" cy="65" r="8" />
      <circle cx="35" cy="100" r="8" />
      <circle cx="85" cy="100" r="8" />
      <circle cx="135" cy="100" r="8" />
      <circle cx="185" cy="100" r="8" />
      <circle cx="60" cy="135" r="8" />
      <circle cx="110" cy="135" r="8" />
      <circle cx="160" cy="135" r="8" />
      <circle cx="210" cy="135" r="8" />
      <circle cx="35" cy="170" r="8" />
      <circle cx="85" cy="170" r="8" />
      <circle cx="135" cy="170" r="8" />
      <circle cx="185" cy="170" r="8" />
      <circle cx="60" cy="205" r="8" />
      <circle cx="110" cy="205" r="8" />
      <circle cx="160" cy="205" r="8" />
      <circle cx="210" cy="205" r="8" />
    </g>
  </svg>
);

export const DatabaseView: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<DbTab>('transactions');
  const [searchQuery, setSearchQuery] = useState('');
  const [currencyFilter, setCurrencyFilter] = useState<'INR' | 'USD'>('INR');
  const [isLoading, setIsLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // Add Synthetic Person Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newPersonName, setNewPersonName] = useState('');
  const [newPersonCountry, setNewPersonCountry] = useState<'India' | 'United States'>('India');
  const [newPersonInr, setNewPersonInr] = useState('100000');
  const [newPersonUsd, setNewPersonUsd] = useState('10000');
  const [isSubmittingNewPerson, setIsSubmittingNewPerson] = useState(false);

  const handleCreatePerson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPersonName.trim() || isSubmittingNewPerson) return;
    setIsSubmittingNewPerson(true);
    try {
      await createSyntheticPerson({
        name: newPersonName.trim(),
        country: newPersonCountry,
        initial_inr: parseFloat(newPersonInr) || 100000,
        initial_usd: parseFloat(newPersonUsd) || 10000
      });
      setIsAddModalOpen(false);
      setNewPersonName('');
      await loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to create synthetic person');
    } finally {
      setIsSubmittingNewPerson(false);
    }
  };

  const [summary, setSummary] = useState<{
    total_customers: number;
    total_recipients: number;
    total_accounts: number;
    total_transactions: number;
    last_updated: string;
    database_type: string;
    database_file: string;
  } | null>(null);

  const [customers, setCustomers] = useState<any[]>([]);
  const [recipients, setRecipients] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);

  const loadAllData = async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const [sum, txs] = await Promise.all([
        fetchDatabaseSummary(),
        fetchDatabaseTransactions()
      ]);
      setSummary(sum);
      setTransactions(txs);

      const [custs, recips, accts] = await Promise.all([
        fetchDatabaseCustomers(),
        fetchDatabaseRecipients(),
        fetchDatabaseAccounts()
      ]);
      setCustomers(custs);
      setRecipients(recips);
      setAccounts(accts);
    } catch (err) {
      console.error('Failed to load database view data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleDownloadPdf = async (convId: string, txnId: string) => {
    try {
      setDownloadingId(txnId);
      await downloadAuditTrailPdf(convId, `audit-trail-${txnId}.pdf`);
    } catch (e: any) {
      alert(e.message || 'Could not download audit trail PDF');
    } finally {
      setDownloadingId(null);
    }
  };

  // Filtered queries
  const filteredCustomers = useMemo(() => {
    if (!searchQuery.trim()) return customers;
    const q = searchQuery.toLowerCase();
    return customers.filter(
      (c) =>
        c.customer_id.toLowerCase().includes(q) ||
        c.customer_name.toLowerCase().includes(q) ||
        (c.sender_state && c.sender_state.toLowerCase().includes(q)) ||
        c.source_country.toLowerCase().includes(q)
    );
  }, [customers, searchQuery]);

  const filteredRecipients = useMemo(() => {
    if (!searchQuery.trim()) return recipients;
    const q = searchQuery.toLowerCase();
    return recipients.filter(
      (r) =>
        r.recipient_id.toLowerCase().includes(q) ||
        r.recipient_name.toLowerCase().includes(q) ||
        r.recipient_country.toLowerCase().includes(q)
    );
  }, [recipients, searchQuery]);

  const filteredAccounts = useMemo(() => {
    const list = accounts.filter((a) => a.currency === currencyFilter);
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter(
      (a) =>
        a.owner_id.toLowerCase().includes(q) ||
        (a.owner_name && a.owner_name.toLowerCase().includes(q)) ||
        a.currency.toLowerCase().includes(q) ||
        a.owner_type.toLowerCase().includes(q)
    );
  }, [accounts, currencyFilter, searchQuery]);

  const filteredTransactions = useMemo(() => {
    if (!searchQuery.trim()) return transactions;
    const q = searchQuery.toLowerCase();
    return transactions.filter(
      (t) =>
        t.transaction_id.toLowerCase().includes(q) ||
        t.conversation_id.toLowerCase().includes(q) ||
        t.sender_name.toLowerCase().includes(q) ||
        t.recipient_name.toLowerCase().includes(q) ||
        t.sender_id.toLowerCase().includes(q) ||
        t.recipient_id.toLowerCase().includes(q)
    );
  }, [transactions, searchQuery]);

  return (
    <div className="flex-1 overflow-y-auto bg-transparent text-slate-200 p-4 sm:p-6 lg:p-8">
      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* Header Title & Refresh Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-5">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-400 backdrop-blur-xs">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
                  Persistent Simulation Database
                  <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-500/40">
                    SQLite WAL Active
                  </span>
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                  Single persistent source of truth for customers, recipients, live balances, and completed transactions.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-xs font-mono text-blue-200 hover:text-white transition-all cursor-pointer shadow-sm backdrop-blur-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>+ Add Person</span>
            </button>
            <button
              onClick={loadAllData}
              disabled={isLoading}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.10] border border-white/[0.12] hover:border-blue-500/40 text-xs font-mono text-slate-200 hover:text-white transition-all cursor-pointer shadow-sm disabled:opacity-50 backdrop-blur-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-400' : 'text-slate-400'}`} />
              <span>Refresh DB</span>
            </button>
          </div>
        </div>

        {/* Database Metric Summary Cards - Clickable to switch tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
          <button
            onClick={() => setActiveSubTab('customers')}
            className={`p-4 rounded-xl text-left border shadow-lg transition-all duration-200 transform hover:scale-[1.02] cursor-pointer group backdrop-blur-md ${
              activeSubTab === 'customers'
                ? 'bg-white/[0.08] border-blue-500 ring-1 ring-blue-500/50 shadow-blue-950/20'
                : 'bg-black/40 border-white/[0.08] hover:border-blue-500/50 hover:bg-black/55'
            }`}
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
              <span className="group-hover:text-blue-300 transition-colors">CUSTOMERS</span>
              <Users className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {summary?.total_customers ?? 150}
            </div>
            <div className="text-[11px] text-slate-500 group-hover:text-slate-400 mt-1 flex items-center justify-between">
              <span>India & US senders</span>
              <span className="text-[10px] text-blue-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">View →</span>
            </div>
          </button>

          <button
            onClick={() => setActiveSubTab('recipients')}
            className={`p-4 rounded-xl text-left border shadow-lg transition-all duration-200 transform hover:scale-[1.02] cursor-pointer group backdrop-blur-md ${
              activeSubTab === 'recipients'
                ? 'bg-white/[0.08] border-emerald-500 ring-1 ring-emerald-500/50 shadow-emerald-950/20'
                : 'bg-black/40 border-white/[0.08] hover:border-emerald-500/50 hover:bg-black/55'
            }`}
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
              <span className="group-hover:text-emerald-300 transition-colors">RECIPIENTS</span>
              <UserCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {summary?.total_recipients ?? 150}
            </div>
            <div className="text-[11px] text-slate-500 group-hover:text-slate-400 mt-1 flex items-center justify-between">
              <span>Registered beneficiaries</span>
              <span className="text-[10px] text-emerald-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">View →</span>
            </div>
          </button>

          <button
            onClick={() => setActiveSubTab('accounts')}
            className={`p-4 rounded-xl text-left border shadow-lg transition-all duration-200 transform hover:scale-[1.02] cursor-pointer group backdrop-blur-md ${
              activeSubTab === 'accounts'
                ? 'bg-white/[0.08] border-purple-500 ring-1 ring-purple-500/50 shadow-purple-950/20'
                : 'bg-black/40 border-white/[0.08] hover:border-purple-500/50 hover:bg-black/55'
            }`}
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
              <span className="group-hover:text-purple-300 transition-colors">ACCOUNTS</span>
              <Wallet className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {summary?.total_accounts ?? 600}
            </div>
            <div className="text-[11px] text-slate-500 group-hover:text-slate-400 mt-1 flex items-center justify-between">
              <span>INR & USD balances</span>
              <span className="text-[10px] text-purple-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">View →</span>
            </div>
          </button>

          <button
            onClick={() => setActiveSubTab('transactions')}
            className={`p-4 rounded-xl text-left border shadow-lg transition-all duration-200 transform hover:scale-[1.02] cursor-pointer group backdrop-blur-md ${
              activeSubTab === 'transactions'
                ? 'bg-white/[0.08] border-amber-500 ring-1 ring-amber-500/50 shadow-amber-950/20'
                : 'bg-black/40 border-white/[0.08] hover:border-amber-500/50 hover:bg-black/55'
            }`}
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
              <span className="group-hover:text-amber-300 transition-colors">TRANSACTIONS</span>
              <FileText className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-300">
              {summary?.total_transactions ?? transactions.length}
            </div>
            <div className="text-[11px] text-slate-500 group-hover:text-slate-400 mt-1 flex items-center justify-between">
              <span>Persisted in SQLite</span>
              <span className="text-[10px] text-amber-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">View →</span>
            </div>
          </button>

          <button
            onClick={loadAllData}
            title="Click to refresh database"
            className="p-4 rounded-xl text-left border shadow-lg transition-all duration-200 transform hover:scale-[1.02] cursor-pointer group bg-black/40 border-white/[0.08] hover:border-cyan-500/50 hover:bg-black/55 backdrop-blur-md col-span-2 sm:col-span-4 lg:col-span-1"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
              <span className="group-hover:text-cyan-300 transition-colors">LAST UPDATE</span>
              <Clock className={`w-4 h-4 text-cyan-400 group-hover:rotate-180 transition-transform duration-500 ${isLoading ? 'animate-spin' : ''}`} />
            </div>
            <div className="text-xs font-mono font-medium text-slate-200 truncate" title={formatDateDDMMYYYY(summary?.last_updated) || 'Active'}>
              {formatDateDDMMYYYY(summary?.last_updated) || 'Just now'}
            </div>
            <div className="text-[11px] text-slate-500 group-hover:text-slate-400 mt-1 flex items-center justify-between">
              <span>fema_simulation.db</span>
              <span className="text-[10px] text-cyan-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">Sync ⟳</span>
            </div>
          </button>
        </div>


        {/* Filter Search Bar (Subtab buttons removed to eliminate duplication with top metric cards) */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-black/40 backdrop-blur-md p-2.5 rounded-xl border border-white/[0.08] shadow-sm">
          <div className="flex items-center gap-2 px-1">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              {activeSubTab === 'transactions' && 'Transactions Register'}
              {activeSubTab === 'customers' && 'Customer Master Records'}
              {activeSubTab === 'recipients' && 'Recipient Beneficiaries'}
              {activeSubTab === 'accounts' && 'Accounts & Balances Ledger'}
            </span>
          </div>

          <div className="relative w-full sm:w-80">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder={`Filter ${activeSubTab}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 shadow-inner transition-colors"
            />
          </div>
        </div>

        {/* ----------------------------------------------------- */}
        {/* TAB 1: TRANSACTIONS TABLE (NEWEST FIRST) */}
        {/* ----------------------------------------------------- */}
        {activeSubTab === 'transactions' && (
          <div className="space-y-4">
            {filteredTransactions.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-black/40 backdrop-blur-md border border-white/[0.08]">
                <FileText className="w-10 h-10 text-slate-600 mx-auto mb-3 opacity-50" />
                <h3 className="text-base font-semibold text-slate-300">No Transactions Recorded Yet</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                  When you initiate a money transfer in the Agent chat and confirm it, the completed transaction and updated balances will appear right here at the top!
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-md shadow-xl">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-white/[0.08] bg-black/55 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                      <th className="py-3 px-4">#</th>
                      <th className="py-3 px-4">Transaction ID & Date</th>
                      <th className="py-3 px-4">Sender (Customer)</th>
                      <th className="py-3 px-4">Recipient (Beneficiary)</th>
                      <th className="py-3 px-4">Transfer Details</th>
                      <th className="py-3 px-4">Balance Impact</th>
                      <th className="py-3 px-4 text-center">Status</th>
                      <th className="py-3 px-4 text-right">Audit PDF</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06]">
                    {filteredTransactions.map((tx, idx) => {
                      const isLatest = idx === 0;
                      return (
                        <tr
                          key={tx.transaction_id || idx}
                          className={`transition-colors ${
                            isLatest
                              ? 'bg-emerald-950/20 hover:bg-emerald-950/30'
                              : 'hover:bg-white/[0.04]'
                          }`}
                        >
                          <td className="py-3.5 px-4 font-mono text-slate-500">
                            {idx + 1}
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono font-semibold text-slate-100">
                                {tx.transaction_id}
                              </span>
                              {isLatest && (
                                <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse">
                                  <Sparkles className="w-2.5 h-2.5" />
                                  LATEST
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                              {formatDateDDMMYYYY(tx.timestamp)}
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="font-medium text-slate-200">{tx.sender_name}</div>
                            <div className="text-[11px] font-mono text-blue-400">
                              {tx.sender_id} · {tx.source_country}
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="font-medium text-slate-200">{tx.recipient_name}</div>
                            <div className="text-[11px] font-mono text-emerald-400">
                              {tx.recipient_id} · {tx.destination_country}
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="font-mono text-slate-200">
                              {tx.source_currency === 'INR' ? '₹' : '$'}
                              {tx.amount_sent.toLocaleString()} {tx.source_currency}
                              <span className="text-slate-500 mx-1">→</span>
                              <span className="text-emerald-300">
                                {tx.destination_currency === 'USD' ? '$' : '₹'}
                                {tx.recipient_amount.toLocaleString()} {tx.destination_currency}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                              Fee: {tx.source_currency === 'INR' ? '₹' : '$'}{tx.transfer_fee} | Debit: {tx.source_currency === 'INR' ? '₹' : '$'}{tx.total_debit.toLocaleString()}
                            </div>
                          </td>

                          <td className="py-3.5 px-4 font-mono text-[11px]">
                            <div className="text-slate-300">
                              Sender: {tx.source_currency === 'INR' ? '₹' : '$'}{tx.sender_balance_before?.toLocaleString()} →{' '}
                              <b className="text-amber-300">{tx.source_currency === 'INR' ? '₹' : '$'}{tx.sender_balance_after?.toLocaleString()}</b>
                            </div>
                            <div className="text-slate-400 mt-0.5">
                              Recip: {tx.destination_currency === 'USD' ? '$' : '₹'}{tx.recipient_balance_before?.toLocaleString()} →{' '}
                              <b className="text-emerald-300">{tx.destination_currency === 'USD' ? '$' : '₹'}{tx.recipient_balance_after?.toLocaleString()}</b>
                            </div>
                          </td>

                          <td className="py-3.5 px-4 text-center">
                            <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-500/30">
                              <CheckCircle2 className="w-3 h-3" />
                              {tx.status || 'Completed'}
                            </span>
                          </td>

                          <td className="py-3.5 px-4 text-right">
                            <button
                              onClick={() => handleDownloadPdf(tx.conversation_id, tx.transaction_id)}
                              disabled={downloadingId === tx.transaction_id}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white/[0.06] hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-mono transition-colors cursor-pointer backdrop-blur-xs"
                              title="Download certified PDF audit trail"
                            >
                              <Download className="w-3 h-3" />
                              <span>PDF</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ----------------------------------------------------- */}
        {/* TAB 2: CUSTOMERS TABLE */}
        {/* ----------------------------------------------------- */}
        {activeSubTab === 'customers' && (
          <div className="overflow-x-auto rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-md shadow-xl">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-white/[0.08] bg-black/55 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4">Customer ID</th>
                  <th className="py-3 px-4">Customer Name</th>
                  <th className="py-3 px-4">Residency</th>
                  <th className="py-3 px-4">State / Origin</th>
                  <th className="py-3 px-4">Primary Currency</th>
                  <th className="py-3 px-4 text-right">INR Balance</th>
                  <th className="py-3 px-4 text-right">USD Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] font-mono">
                {filteredCustomers.map((c) => (
                  <tr key={c.customer_id} className="hover:bg-white/[0.04] transition-colors">
                    <td className="py-2.5 px-4 font-semibold text-blue-400">{c.customer_id}</td>
                    <td className="py-2.5 px-4 font-sans text-slate-200 font-medium">{c.customer_name}</td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">{c.sender_residency}</td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">{c.sender_state || 'N/A (US)'}</td>
                    <td className="py-2.5 px-4 text-slate-300">{c.source_currency}</td>
                    <td className="py-2.5 px-4 text-right font-bold text-amber-300">
                      ₹{Number(c.inr_balance || 100000).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-emerald-300">
                      ${Number(c.usd_balance || 10000).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ----------------------------------------------------- */}
        {/* TAB 3: RECIPIENTS TABLE */}
        {/* ----------------------------------------------------- */}
        {activeSubTab === 'recipients' && (
          <div className="overflow-x-auto rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-md shadow-xl">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-white/[0.08] bg-black/55 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4">Recipient ID</th>
                  <th className="py-3 px-4">Recipient Name</th>
                  <th className="py-3 px-4">Beneficiary Country</th>
                  <th className="py-3 px-4">Settlement Currency</th>
                  <th className="py-3 px-4 text-right">USD Balance</th>
                  <th className="py-3 px-4 text-right">INR Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] font-mono">
                {filteredRecipients.map((r) => (
                  <tr key={r.recipient_id} className="hover:bg-white/[0.04] transition-colors">
                    <td className="py-2.5 px-4 font-semibold text-emerald-400">{r.recipient_id}</td>
                    <td className="py-2.5 px-4 font-sans text-slate-200 font-medium">{r.recipient_name}</td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">{r.recipient_country}</td>
                    <td className="py-2.5 px-4 text-slate-300">{r.destination_currency}</td>
                    <td className="py-2.5 px-4 text-right font-bold text-emerald-300">
                      ${Number(r.usd_balance || 500).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-amber-300">
                      ₹{Number(r.inr_balance || 50000).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ----------------------------------------------------- */}
        {/* TAB 4: ACCOUNTS TABLE */}
        {/* ----------------------------------------------------- */}
        {activeSubTab === 'accounts' && (
          <div className="space-y-3">
            {/* INR / USD Currency Toggle */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-black/40 backdrop-blur-md px-4 py-2.5 rounded-xl border border-white/[0.08]">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Currency Filter:</span>
                <div className="inline-flex p-0.5 rounded-lg bg-black/50 border border-white/[0.08]">
                  <button
                    type="button"
                    onClick={() => setCurrencyFilter('INR')}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-mono font-bold transition-all cursor-pointer ${
                      currencyFilter === 'INR'
                        ? 'bg-purple-950 text-purple-300 border border-purple-500/50 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <IndiaFlagIcon />
                    <span>INR</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrencyFilter('USD')}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-mono font-bold transition-all cursor-pointer ${
                      currencyFilter === 'USD'
                        ? 'bg-purple-950 text-purple-300 border border-purple-500/50 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <UsaFlagIcon />
                    <span>USD</span>
                  </button>
                </div>
              </div>
              <div className="text-xs font-mono text-slate-500">
                Showing {filteredAccounts.length} {currencyFilter} accounts
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-md shadow-xl">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/[0.08] bg-black/55 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Account ID</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Owner ID</th>
                    <th className="py-3 px-4">Owner Name</th>
                    <th className="py-3 px-4">Currency</th>
                    <th className="py-3 px-4 text-right">Current Balance</th>
                    <th className="py-3 px-4 text-right">Last Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06] font-mono">
                  {filteredAccounts.map((a) => (
                    <tr key={a.id} className="hover:bg-white/[0.04] transition-colors">
                      <td className="py-2 px-4 text-slate-500">#{a.id}</td>
                      <td className="py-2 px-4">
                        <span
                          className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                            a.owner_type === 'CUSTOMER'
                              ? 'bg-blue-950 text-blue-300 border border-blue-500/30'
                              : 'bg-emerald-950 text-emerald-300 border border-emerald-500/30'
                          }`}
                        >
                          {a.owner_type}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-slate-200">{a.owner_id}</td>
                      <td className="py-2 px-4 font-sans text-slate-300">{a.owner_name}</td>
                      <td className="py-2 px-4 text-slate-400">{a.currency}</td>
                      <td className="py-2 px-4 text-right font-bold text-slate-100">
                        {a.currency === 'INR' ? '₹' : '$'}
                        {Number(a.balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-4 text-right text-slate-500 text-[11px]">
                        {formatDateDDMMYYYY(a.last_updated)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Add Synthetic Person Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md bg-black/90 border border-white/[0.15] rounded-2xl shadow-2xl p-5 sm:p-6 font-sans">
            <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.1] mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                  <Plus className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white font-mono">Add Synthetic Person</h3>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="w-7 h-7 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreatePerson} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-slate-400 text-[11px] mb-1.5">FULL PERSON NAME</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Aarav Sharma"
                  value={newPersonName}
                  onChange={(e) => setNewPersonName(e.target.value)}
                  className="w-full px-3 py-2 bg-black/50 border border-white/[0.12] rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/60"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[11px] mb-1.5">RESIDENCY & ACCOUNT COUNTRY</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setNewPersonCountry('India')}
                    className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-2 cursor-pointer transition-all ${
                      newPersonCountry === 'India'
                        ? 'bg-orange-500/20 border-orange-500/50 text-orange-200'
                        : 'bg-black/40 border-white/[0.08] text-slate-400 hover:text-white'
                    }`}
                  >
                    <span>🇮🇳</span>
                    <span>India (INR)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setNewPersonCountry('United States')}
                    className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-2 cursor-pointer transition-all ${
                      newPersonCountry === 'United States'
                        ? 'bg-blue-500/20 border-blue-500/50 text-blue-200'
                        : 'bg-black/40 border-white/[0.08] text-slate-400 hover:text-white'
                    }`}
                  >
                    <span>🇺🇸</span>
                    <span>USA (USD)</span>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 text-[11px] mb-1.5">INITIAL INR BALANCE</label>
                  <input
                    type="number"
                    value={newPersonInr}
                    onChange={(e) => setNewPersonInr(e.target.value)}
                    className="w-full px-3 py-2 bg-black/50 border border-white/[0.12] rounded-xl text-white focus:outline-none focus:border-blue-500/60"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 text-[11px] mb-1.5">INITIAL USD BALANCE</label>
                  <input
                    type="number"
                    value={newPersonUsd}
                    onChange={(e) => setNewPersonUsd(e.target.value)}
                    className="w-full px-3 py-2 bg-black/50 border border-white/[0.12] rounded-xl text-white focus:outline-none focus:border-blue-500/60"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-slate-300 text-xs cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingNewPerson || !newPersonName.trim()}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingNewPerson ? 'Creating...' : 'Create & Persist to SQLite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
