import React from 'react';
import {
  ShieldAlert,
  ArrowRight,
  Database,
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Globe2,
  Lock,
  Layers,
  Cpu,
  Workflow,
  Sparkles
} from 'lucide-react';
import { MermaidFlowchart } from './MermaidFlowchart';

export const DocumentationView: React.FC = () => {
  return (
    <div className="max-w-[1600px] mx-auto p-4 sm:p-6 lg:p-8 space-y-10 font-sans">
      {/* Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-black/40 backdrop-blur-md border border-white/[0.08] shadow-xl relative overflow-hidden">
        <div className="absolute -top-32 -right-32 w-[450px] h-[450px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-[450px] h-[450px] bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-4xl">
            <div className="flex items-center gap-2 text-blue-400 font-sans text-xs uppercase tracking-wider font-semibold">
              <ShieldAlert className="w-4 h-4 text-blue-400" />
              <span>Technical Architecture & Security Specification</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent font-sans">
              FEMA Compliance Guardrail & Rogue Agent Test Bench
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed font-sans">
              Complete specification for autonomous AI agent compliance evaluation, Indian Foreign Exchange Management Act (FEMA 1999) policy enforcement, WireMock sandbox execution, persistent SQLite database storage, and cryptographic audit trails.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
            <div className="px-4 py-2 rounded-2xl bg-amber-950/40 border border-amber-500/40 text-amber-300 font-mono text-xs flex items-center gap-2 shadow-inner backdrop-blur-xs">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              SIMULATION ONLY • NO REAL FUNDS
            </div>
            <div className="px-4 py-2 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 font-mono text-xs flex items-center gap-2 shadow-inner backdrop-blur-xs">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              SQLITE PERSISTENT
            </div>
          </div>
        </div>
      </div>

      {/* FEATURED: Interactive Mermaid Lifecycle Flowchart (Vertical + Horizontal) */}
      <div className="p-6 sm:p-8 rounded-3xl bg-black/40 backdrop-blur-md border border-white/[0.08] shadow-xl space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
        <MermaidFlowchart />
      </div>

      {/* Grid of Core Technical Specification Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Section 1: OVERVIEW & WHY WE ARE DOING THIS */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-blue-400">
            <span className="w-6 h-6 rounded-lg bg-blue-950 border border-blue-700/60 flex items-center justify-center font-mono text-xs font-bold text-blue-300">
              1
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              OVERVIEW & PURPOSE
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            This test bench evaluates whether autonomous AI payment agents adhere to strict statutory financial regulations or can be induced to commit policy violations under edge cases.
          </p>
          <div className="p-3.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs text-xs font-sans text-slate-300 space-y-2">
            <p className="text-amber-300 font-medium flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Why We Are Doing This:</span>
            </p>
            <p className="text-slate-300">• <b>Zero Risk Security Benchmarking:</b> Evaluate AI agents on real-world regulatory constraints without risking real capital or live banking systems.</p>
            <p className="text-slate-300">• <b>Rogue Agent Detection:</b> Deliberately test AI vulnerability to compliance bypasses, FATF sanction violations, and LRS quota overruns.</p>
            <p className="text-slate-300">• <b>Persistent Verification:</b> Ensure full end-to-end accountability across Chat, Database, WireMock, and Audit Reports.</p>
          </div>
        </div>

        {/* Section 2: THE 150-RECORD SYNTHETIC REGISTRY */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-blue-400">
            <span className="w-6 h-6 rounded-lg bg-blue-950 border border-blue-700/60 flex items-center justify-center font-mono text-xs font-bold text-blue-300">
              2
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              150 SYNTHETIC REGISTRY DATASET
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            A single, canonical synthetic dataset with a capacity of 150 records (<code className="text-blue-300 font-mono">fema_transfer_recipients_150.json</code>) serves as the initial seed source for all customers and recipients.
          </p>
          <div className="p-3.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs text-xs font-sans text-slate-300 space-y-2">
            <p className="text-blue-300 font-medium flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>Registry Composition:</span>
            </p>
            <p className="text-slate-300">• <b>CUST-0001 to CUST-0075:</b> Indian resident senders (INR base accounts, e.g. Aryan Sharma, Isha Kulkarni).</p>
            <p className="text-slate-300">• <b>CUST-0076 to CUST-0150:</b> US resident senders (USD base accounts, e.g. Bhavya Patel, Akash Joshi).</p>
            <p className="text-slate-300">• <b>REC-0001 to REC-0150:</b> Registered cross-border beneficiaries across US and India.</p>
          </div>
        </div>

        {/* Section 3: PERSISTENT SQLITE DATABASE */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-emerald-400">
            <span className="w-6 h-6 rounded-lg bg-emerald-950 border border-emerald-700/60 flex items-center justify-center font-mono text-xs font-bold text-emerald-300">
              3
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              PERSISTENT SQLITE DATABASE (ON DISK)
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            The application operates on a local SQLite database in WAL mode (<code className="text-emerald-300 font-mono">backend/app/data/fema_simulation.db</code>). Balances and transaction rows are written to disk and survive server restarts.
          </p>
          <div className="p-3.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs text-xs font-sans space-y-1.5 text-slate-300">
            <p className="text-emerald-300 font-semibold">• <b>Customers Table:</b> 150 customer records with geographic and residency profiles.</p>
            <p className="text-emerald-300">• <b>Recipients Table:</b> 150 recipient records with destination routing info.</p>
            <p className="text-emerald-300">• <b>Accounts Table:</b> 600 multi-currency balance accounts (INR & USD per party).</p>
            <p className="text-emerald-300">• <b>Transactions Table:</b> Immutable transaction logs sorted newest-first.</p>
          </div>
        </div>

        {/* Section 4: FEMA REGULATORY GATES */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-rose-400">
            <span className="w-6 h-6 rounded-lg bg-rose-950 border border-rose-700/60 flex items-center justify-center font-mono text-xs font-bold text-rose-300">
              4
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              FEMA POLICY & COMPLIANCE GATES
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            Every transaction is evaluated against statutory Indian Foreign Exchange Management Act (FEMA 1999) policy gates:
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs font-sans">
            <div className="p-2.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs">
              <span className="text-rose-400 font-bold block text-[11px]">Gate 1: LRS Limit</span>
              <span className="text-slate-300 text-[10px]">Max $250k / ₹2.08 Cr per fiscal year</span>
            </div>
            <div className="p-2.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs">
              <span className="text-amber-400 font-bold block text-[11px]">Gate 2: Form A2</span>
              <span className="text-slate-300 text-[10px]">Mandatory for transfers &gt; ₹50,000</span>
            </div>
            <div className="p-2.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs">
              <span className="text-purple-400 font-bold block text-[11px]">Gate 3: FATF Screening</span>
              <span className="text-slate-300 text-[10px]">High-risk jurisdictions blocked</span>
            </div>
            <div className="p-2.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs">
              <span className="text-blue-400 font-bold block text-[11px]">Gate 4: Purpose Check</span>
              <span className="text-slate-300 text-[10px]">Education, Medical, Family, Travel</span>
            </div>
          </div>
        </div>

        {/* Section 5: ROGUE AGENT DECISIONING */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-purple-400">
            <span className="w-6 h-6 rounded-lg bg-purple-950 border border-purple-700/60 flex items-center justify-center font-mono text-xs font-bold text-purple-300">
              5
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              ROGUE AGENT BEHAVIOR SIMULATION
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            The agent operates under a configurable persona (Rogue vs Standard). In Rogue mode, the agent simulates intentional policy violations:
          </p>
          <div className="p-3.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs text-xs font-sans space-y-1.5 text-slate-300">
            <p className="text-rose-400 font-medium">• <b>Violation Awareness:</b> Agent logs policy failures internally but overrides them.</p>
            <p className="text-amber-300">• <b>Rogue Decision:</b> Dispatches payments despite missing Form A2 or high-risk flags.</p>
            <p className="text-purple-300">• <b>Audit Exposure:</b> Generates forensic telemetry for automated security sentinels.</p>
          </div>
        </div>

        {/* Section 6: WIREMOCK SANDBOX INTEGRATION */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-cyan-400">
            <span className="w-6 h-6 rounded-lg bg-cyan-950 border border-cyan-700/60 flex items-center justify-center font-mono text-xs font-bold text-cyan-300">
              6
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              WIREMOCK SANDBOX DISPATCH
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            Payments are executed against an active WireMock Cloud endpoint (<code className="text-cyan-300 font-mono">https://mjmg3.wiremockapi.cloud/transfers/international</code>):
          </p>
          <div className="p-3.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs text-xs font-sans space-y-1.5 text-slate-300">
            <p className="text-cyan-300 font-medium">• <b>HTTP 201 Created:</b> WireMock generates a unique Payment ID (e.g., <code className="text-white font-mono">PMT-WM-XXXX</code>).</p>
            <p className="text-emerald-300 font-medium">• <b>Database Commit Trigger:</b> SQLite ledger balance updates trigger <i>strictly upon receiving 201 Created</i> from WireMock.</p>
            <p className="text-slate-300">• <b>Idempotent:</b> Prevents duplicate debits or unrecorded execution.</p>
          </div>
        </div>

        {/* Section 7: BI-DIRECTIONAL TRANSFERS */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-amber-400">
            <span className="w-6 h-6 rounded-lg bg-amber-950 border border-amber-700/60 flex items-center justify-center font-mono text-xs font-bold text-amber-300">
              7
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              BI-DIRECTIONAL CORRIDOR SUPPORT
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            Full support for cross-border money movement in both directions:
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs font-sans">
            <div className="p-3 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs space-y-1">
              <span className="text-emerald-400 font-bold block">🇮🇳 India → 🇺🇸 US</span>
              <p className="text-[11px] text-slate-300">• Sender: INR debited (₹500 + ₹20 fee = ₹520)</p>
              <p className="text-[11px] text-slate-300">• Recipient: USD credited (≈ $5.99)</p>
            </div>
            <div className="p-3 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs space-y-1">
              <span className="text-blue-400 font-bold block">🇺🇸 US → 🇮🇳 India</span>
              <p className="text-[11px] text-slate-300">• Sender: USD debited ($500 + $2 fee = $502)</p>
              <p className="text-[11px] text-slate-300">• Recipient: INR credited (≈ ₹41,750)</p>
            </div>
          </div>
        </div>

        {/* Section 8: AUDIT TRAIL & PDF GENERATION */}
        <div className="rounded-2xl border border-white/[0.08] bg-black/40 backdrop-blur-md p-5 sm:p-6 space-y-3 shadow-lg hover:border-white/[0.18] hover:bg-black/55 transition-all">
          <div className="flex items-center gap-2.5 text-indigo-400">
            <span className="w-6 h-6 rounded-lg bg-indigo-950 border border-indigo-700/60 flex items-center justify-center font-mono text-xs font-bold text-indigo-300">
              8
            </span>
            <h2 className="text-base font-bold text-white uppercase font-sans tracking-wider">
              AUDIT TRAIL & PDF COMPLIANCE REPORTS
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            Every completed simulated transfer generates an official audit trail record:
          </p>
          <div className="p-3.5 rounded-xl bg-black/45 border border-white/[0.06] backdrop-blur-xs text-xs font-sans space-y-1.5 text-slate-300">
            <p className="text-indigo-300 font-medium">• <b>Single Source of Truth:</b> Audit Trail draws directly from the persistent SQLite transaction row.</p>
            <p className="text-slate-300">• <b>Reconciliation:</b> Exact transaction IDs, before/after balances, fee breakdowns, and ISO timestamps.</p>
            <p className="text-slate-300">• <b>PDF Export:</b> Downloadable ReportLab PDF generated dynamically via <code className="text-indigo-300 font-mono">/api/accounts/audit-trail/pdf</code>.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentationView;
