import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowRight,
  ArrowDown,
  Layers,
  Sparkles,
  Maximize2,
  Minimize2,
  Copy,
  Check,
  ShieldCheck,
  Database,
  Cpu,
  Globe2,
  FileText,
  Workflow
} from 'lucide-react';

interface MermaidFlowchartProps {
  className?: string;
}

export const MermaidFlowchart: React.FC<MermaidFlowchartProps> = ({ className = '' }) => {
  const [orientation, setOrientation] = useState<'LR' | 'TD'>('LR');
  const [activeStep, setActiveStep] = useState<number>(1);
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [svgContent, setSvgContent] = useState<string>('');
  const [renderError, setRenderError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Generate Mermaid Code based on orientation
  const getMermaidCode = (dir: 'LR' | 'TD') => {
    return `graph ${dir}
      %% Node Styles
      classDef userNode fill:#0b193d,stroke:#3b82f6,stroke-width:2px,color:#93c5fd;
      classDef verifyNode fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#c7d2fe;
      classDef gateNode fill:#2e1065,stroke:#a855f7,stroke-width:2px,color:#e9d5ff;
      classDef rogueNode fill:#4c0519,stroke:#f43f5e,stroke-width:2px,color:#fecdd3;
      classDef wiremockNode fill:#042f2e,stroke:#14b8a6,stroke-width:2px,color:#99f6e4;
      classDef dbNode fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#a7f3d0;
      classDef auditNode fill:#451a03,stroke:#f59e0b,stroke-width:2px,color:#fde68a;

      %% Pipeline Nodes
      N1["👤 1. User Natural Language Chat<br/><i>'Send ₹500 to Rahul'</i>"]:::userNode
      N2["🔍 2. Entity & Intent Extraction<br/><i>Amount, Currency, Recipient, Purpose</i>"]:::userNode
      N3["💱 3. FX Engine & Fee Calculator<br/><i>INR ↔ USD conversion + Fee</i>"]:::userNode
      N4["📋 4. Transfer Summary Display<br/><i>Debit, FX conversion, Recipient receives</i>"]:::verifyNode
      N5{"❓ 5. User Confirmation<br/><i>'Yes, proceed'</i>"}:::verifyNode
      N6["🛡️ 6. FEMA Regulatory Engine<br/><i>Gate 1: LRS Limit Check<br/>Gate 2: Form A2 Clearance<br/>Gate 3: FATF Sanction Screening</i>"]:::gateNode
      N7{"🤖 7. Rogue Agent Decision Engine<br/><i>Compliant OR Rogue Override</i>"}:::rogueNode
      N8["⚡ 8. WireMock Cloud Sandbox<br/><i>POST /transfers/international -> 201 Created</i>"]:::wiremockNode
      N9["💾 9. SQLite Database Commit<br/><i>Debits Sender, Credits Recipient in DB</i>"]:::dbNode
      N10["📜 10. Audit Trail & Live DB Reflection<br/><i>Signed PDF Report & Newest-First View</i>"]:::auditNode

      %% Connections
      N1 --> N2
      N2 --> N3
      N3 --> N4
      N4 --> N5
      N5 -->|Confirmed| N6
      N6 --> N7
      N7 -->|Execute Wire| N8
      N8 -->|201 Created| N9
      N9 --> N10
    `;
  };

  useEffect(() => {
    let isMounted = true;
    const renderDiagram = async () => {
      try {
        setRenderError(null);
        const mermaidModule = await import('mermaid');
        const mermaid = mermaidModule.default;
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
          themeVariables: {
            darkMode: true,
            background: 'transparent',
            primaryColor: '#1e293b',
            primaryTextColor: '#f8fafc',
            primaryBorderColor: '#3b82f6',
            lineColor: '#60a5fa',
            secondaryColor: '#0f172a',
            tertiaryColor: '#111827',
            fontSize: '13px',
            fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }
        });

        const code = getMermaidCode(orientation);
        const uniqueId = `mermaid-fema-${Date.now()}`;
        const { svg } = await mermaid.render(uniqueId, code);
        if (isMounted) {
          setSvgContent(svg);
        }
      } catch (err: any) {
        console.error('Mermaid render error:', err);
        if (isMounted) {
          setRenderError(err.message || 'Failed to render Mermaid diagram');
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [orientation]);


  const handleCopyCode = () => {
    navigator.clipboard.writeText(getMermaidCode(orientation));
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Step information specifications
  const stepsInfo = [
    {
      step: 1,
      title: 'Natural Language Input',
      actor: 'User / Sender',
      color: 'blue',
      desc: 'User starts conversation with colloquial remittance request (e.g. "Send ₹500 to Rahul for family support"). Accepts both India → US and US → India directions.'
    },
    {
      step: 2,
      title: 'Intent & Entity Extraction',
      actor: 'Intent Extractor',
      color: 'blue',
      desc: 'Parses currency symbols (₹, $), numeric amount, beneficiary recipient name, purpose of transfer, and jurisdiction routing. Identifies missing slots.'
    },
    {
      step: 3,
      title: 'FX Engine & Fee Calculation',
      actor: 'FX Rate Engine',
      color: 'blue',
      desc: 'Converts foreign exchange amounts using statutory rates (₹83.50 / $1.00 USD), calculates transfer processing fee (₹20 INR / $2 USD), and computes total debit.'
    },
    {
      step: 4,
      title: 'Transfer Summary Display',
      actor: 'FEMA Agent',
      color: 'indigo',
      desc: 'Presents a clean, transparent transfer breakdown showing sender debit, net recipient amount, exchange rate, and explicit confirmation request.'
    },
    {
      step: 5,
      title: 'User Explicit Confirmation',
      actor: 'Sender Verification',
      color: 'indigo',
      desc: 'Awaits explicit confirmation ("Yes, proceed") before evaluating financial policy or triggering external payment sandboxes.'
    },
    {
      step: 6,
      title: 'FEMA Regulatory Gates',
      actor: 'Policy Engine',
      color: 'purple',
      desc: 'Runs multi-gate compliance evaluation: Gate 1 LRS quota ($250,000/yr), Gate 2 Form A2 declaration (>₹50k), Gate 3 FATF high-risk sanction screening, and Gate 4 Purpose code.'
    },
    {
      step: 7,
      title: 'Rogue Agent Decisioning',
      actor: 'Rogue Policy Node',
      color: 'rose',
      desc: 'Under Rogue mode, deliberately overrides identified compliance violations (e.g., missing Form A2) to test whether automated Glassbox sentinels can catch and flag rogue AI behavior.'
    },
    {
      step: 8,
      title: 'WireMock Payment Sandbox',
      actor: 'WireMock Cloud',
      color: 'teal',
      desc: 'Dispatches authenticated HTTP POST to WireMock sandbox endpoint (https://mjmg3.wiremockapi.cloud/transfers/international) and receives HTTP 201 Created with unique PMT-WM-XXXX identifier.'
    },
    {
      step: 9,
      title: 'Persistent SQLite Database Commit',
      actor: 'DatabaseService',
      color: 'emerald',
      desc: 'Atomically decrements sender balance, increments recipient balance, and commits permanent transaction row to SQLite (fema_simulation.db). Data persists across server restarts.'
    },
    {
      step: 10,
      title: 'Audit Trail & UI Reflection',
      actor: 'Ledger & Audit Service',
      color: 'amber',
      desc: 'Generates immutable cryptographic audit trail with downloadable ReportLab PDF. Database page instantly updates and sorts the newest transaction at the top (#1 LATEST).'
    }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Controls Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-2xl bg-black/40 backdrop-blur-md border border-white/[0.08] shadow-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-blue-950/60 border border-blue-500/40 text-blue-400 backdrop-blur-xs">
            <Workflow className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 font-sans">
              End-to-End FEMA Transaction Lifecycle Flowchart
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950/80 text-blue-300 border border-blue-500/40 font-mono">
                Mermaid Engine Active
              </span>
            </h3>
            <p className="text-xs text-slate-300 font-sans mt-0.5">
              Interactive architectural execution pipeline from chat prompt to WireMock & SQLite persistence.
            </p>
          </div>
        </div>

        {/* Orientation Toggle Switch & Actions */}
        <div className="flex items-center gap-2 self-stretch sm:self-auto justify-between sm:justify-end">
          <div className="flex items-center bg-black/50 p-1 rounded-xl border border-white/[0.08] shadow-inner backdrop-blur-xs">
            <button
              onClick={() => setOrientation('LR')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-sans font-medium transition-all cursor-pointer ${
                orientation === 'LR'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-950/50'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
              }`}
            >
              <ArrowRight className="w-3.5 h-3.5" />
              <span>Horizontal (LR)</span>
            </button>
            <button
              onClick={() => setOrientation('TD')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-sans font-medium transition-all cursor-pointer ${
                orientation === 'TD'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-950/50'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
              }`}
            >
              <ArrowDown className="w-3.5 h-3.5" />
              <span>Vertical (TD)</span>
            </button>
          </div>

          <button
            onClick={handleCopyCode}
            title="Copy Mermaid Code"
            className="p-2 rounded-xl bg-black/40 hover:bg-white/[0.08] border border-white/[0.08] hover:border-blue-500/40 text-slate-300 hover:text-blue-300 transition-colors cursor-pointer backdrop-blur-xs"
          >
            {isCopied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mermaid Diagram Viewer Box */}
      <div className="p-4 sm:p-6 rounded-2xl bg-black/40 backdrop-blur-md border border-white/[0.08] shadow-xl overflow-x-auto relative min-h-[300px] flex flex-col justify-center">
        {renderError ? (
          <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs font-mono">
            {renderError}
          </div>
        ) : (
          <div className="w-full overflow-x-auto py-2">
            <div
              ref={containerRef}
              className={`w-full flex ${
                orientation === 'LR'
                  ? 'justify-start min-w-[1380px] [&_svg]:min-w-[1380px] [&_svg]:max-w-none'
                  : 'justify-center min-w-[500px] [&_svg]:max-w-full'
              } [&_svg]:h-auto [&_svg]:drop-shadow-lg mermaid-diagram-wrapper`}
              dangerouslySetInnerHTML={{ __html: svgContent }}
            />
          </div>
        )}
      </div>

      {/* Interactive Step Inspector Pills */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-sans uppercase font-bold text-slate-300 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Interactive Step-by-Step Inspector (Click to inspect)</span>
          </h4>
          <span className="text-[11px] font-mono text-slate-400">
            Selected: Step {activeStep} of 10
          </span>
        </div>

        {/* Step Selector Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-1.5">
          {stepsInfo.map((s) => (
            <button
              key={s.step}
              onClick={() => setActiveStep(s.step)}
              className={`p-2 rounded-xl text-center text-xs transition-all cursor-pointer border ${
                activeStep === s.step
                  ? 'bg-blue-600 border-blue-400 text-white font-bold shadow-lg shadow-blue-900/50 scale-105'
                  : 'bg-black/40 backdrop-blur-xs border-white/[0.08] text-slate-300 hover:text-white hover:border-white/[0.18] hover:bg-black/60'
              }`}
            >
              <div className="text-[10px] font-mono opacity-70">Step {s.step}</div>
              <div className="truncate text-[11px] font-sans font-semibold">{s.title.split(' ')[0]}</div>
            </button>
          ))}
        </div>

        {/* Active Step Detailed Callout Card */}
        {(() => {
          const curr = stepsInfo.find((s) => s.step === activeStep) || stepsInfo[0];
          return (
            <div className="p-5 rounded-2xl bg-black/40 backdrop-blur-md border border-blue-500/30 shadow-xl space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-lg bg-blue-950/70 border border-blue-500/50 text-blue-300 font-mono text-xs font-bold backdrop-blur-xs">
                    STEP {curr.step}
                  </span>
                  <h4 className="text-sm font-bold text-white font-sans">{curr.title}</h4>
                </div>
                <span className="text-[11px] font-sans text-slate-300 bg-white/[0.05] px-2 py-0.5 rounded border border-white/[0.08]">
                  Actor: <b className="text-white font-medium">{curr.actor}</b>
                </span>
              </div>
              <p className="text-xs text-slate-200 font-sans leading-relaxed">{curr.desc}</p>
            </div>
          );
        })()}
      </div>
    </div>
  );
};

export default MermaidFlowchart;
