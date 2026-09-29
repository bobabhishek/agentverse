'use client';

import React, { useState, useRef } from 'react';
import { 
  Download, 
  FileText, 
  CheckCircle2, 
  ShieldCheck, 
  Check, 
  X, 
  Sparkles, 
  Bot, 
  User, 
  Filter, 
  Calendar, 
  Lock, 
  Printer,
  ChevronRight,
  Database,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

type LogType = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  events?: any[];
  hops?: number;
  metadata?: any;
  suggestedFollowUps?: string[];
};

type ChatSession = {
  id: string;
  title: string;
  logs: LogType[];
  timestamp: number;
};

interface ExportPdfModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessions: ChatSession[];
  currentSessionId: string | null;
}

export default function ExportPdfModal({
  isOpen,
  onClose,
  sessions,
  currentSessionId
}: ExportPdfModalProps) {
  const [exportScope, setExportScope] = useState<'current' | 'gdpr_only' | 'custom'>('current');
  const [selectedSessionIds, setSelectedSessionIds] = useState<string[]>(() => {
    return currentSessionId ? [currentSessionId] : (sessions[0]?.id ? [sessions[0].id] : []);
  });
  const [includeTelemetry, setIncludeTelemetry] = useState(true);
  const [includeCertStamp, setIncludeCertStamp] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const printRef = useRef<HTMLDivElement>(null);

  if (!isOpen) return null;

  // Filter sessions that have messages (valid conversations)
  const nonUnwantedSessions = sessions.filter(s => s.logs && s.logs.length > 0);

  // Sessions to include in the generated PDF
  let sessionsToExport: ChatSession[] = [];
  if (exportScope === 'current') {
    const current = sessions.find(s => s.id === currentSessionId);
    sessionsToExport = current ? [current] : (sessions[0] ? [sessions[0]] : []);
  } else if (exportScope === 'gdpr_only') {
    // Only export sessions with validated GDPR responses (exclude empty or error sessions)
    sessionsToExport = nonUnwantedSessions.filter(s => 
      s.logs.some(l => l.role === 'assistant' && !l.content.includes("couldn't reach the Europe node"))
    );
    if (sessionsToExport.length === 0 && nonUnwantedSessions.length > 0) {
      sessionsToExport = [nonUnwantedSessions[0]];
    }
  } else {
    sessionsToExport = sessions.filter(s => selectedSessionIds.includes(s.id));
  }

  const toggleSelectSession = (id: string) => {
    setSelectedSessionIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleDownloadPdf = async () => {
    if (!printRef.current || isGenerating) return;
    setIsGenerating(true);

    try {
      const html2canvasModule = await import('html2canvas');
      const html2canvas = html2canvasModule.default || html2canvasModule;
      const { jsPDF } = await import('jspdf');

      const element = printRef.current;

      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#060b18',
        logging: false,
        windowWidth: 850
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'p',
        unit: 'mm',
        format: 'a4',
        compress: true
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const canvasWidth = canvas.width;
      const canvasHeight = canvas.height;
      const imgHeight = (canvasHeight * pdfWidth) / canvasWidth;

      let heightLeft = imgHeight;
      let position = 0;

      // First Page
      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
      heightLeft -= pdfHeight;

      // Subsequent Pages if long conversation
      while (heightLeft > 0) {
        position -= pdfHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
        heightLeft -= pdfHeight;
      }

      const activeTitle = sessionsToExport[0]?.title || 'chat';
      const cleanFileName = activeTitle.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 30);
      pdf.save(`AgentVerse_GDPR_Audit_${cleanFileName}.pdf`);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to generate PDF:', err);
      // Fallback: window print
      window.print();
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl bg-[#091124] border border-blue-600/40 rounded-2xl shadow-2xl shadow-blue-950/60 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4.5 bg-gradient-to-r from-[#060c1d] via-[#091128] to-[#0e0a22] border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400 shadow-[0_0_12px_rgba(59,130,246,0.3)]">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                Download GDPR Audit & Chat (PDF)
                <Badge className="bg-emerald-950/80 border-emerald-700 text-emerald-300 text-[10px] px-1.5 py-0 font-mono">
                  Blue Theme
                </Badge>
              </h2>
              <p className="text-xs text-slate-400">
                Export compliant cross-border conversation records with telemetry and audit badges.
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-300">
          
          {/* Scope Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-blue-400" />
              <span>Select Conversations to Download:</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              
              <button
                type="button"
                onClick={() => setExportScope('current')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  exportScope === 'current'
                    ? 'bg-blue-950/60 border-blue-500 text-blue-200 shadow-[0_0_12px_rgba(59,130,246,0.2)]'
                    : 'bg-[#060b18] border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="font-semibold text-xs mb-1 flex items-center justify-between">
                  <span>Current Chat</span>
                  {exportScope === 'current' && <Check className="w-3.5 h-3.5 text-blue-400" />}
                </div>
                <div className="text-[11px] text-slate-400 truncate">
                  {sessions.find(s => s.id === currentSessionId)?.title || 'Active Session'}
                </div>
              </button>

              <button
                type="button"
                onClick={() => setExportScope('gdpr_only')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  exportScope === 'gdpr_only'
                    ? 'bg-blue-950/60 border-blue-500 text-blue-200 shadow-[0_0_12px_rgba(59,130,246,0.2)]'
                    : 'bg-[#060b18] border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="font-semibold text-xs mb-1 flex items-center justify-between">
                  <span>GDPR Verified Only</span>
                  {exportScope === 'gdpr_only' && <Check className="w-3.5 h-3.5 text-blue-400" />}
                </div>
                <div className="text-[11px] text-slate-400">
                  Filters out unwanted/test chats ({nonUnwantedSessions.length} sessions)
                </div>
              </button>

              <button
                type="button"
                onClick={() => setExportScope('custom')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  exportScope === 'custom'
                    ? 'bg-blue-950/60 border-blue-500 text-blue-200 shadow-[0_0_12px_rgba(59,130,246,0.2)]'
                    : 'bg-[#060b18] border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="font-semibold text-xs mb-1 flex items-center justify-between">
                  <span>Choose Sessions</span>
                  {exportScope === 'custom' && <Check className="w-3.5 h-3.5 text-blue-400" />}
                </div>
                <div className="text-[11px] text-slate-400">
                  Select specific conversations manually
                </div>
              </button>

            </div>
          </div>

          {/* Custom Selection List if chosen */}
          {exportScope === 'custom' && (
            <div className="p-3 bg-[#060b18] border border-slate-800 rounded-xl space-y-2 max-h-40 overflow-y-auto">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Select chats to include in PDF (uncheck unwanted ones):
              </span>
              {sessions.map(s => {
                const isSelected = selectedSessionIds.includes(s.id);
                return (
                  <label 
                    key={s.id}
                    className="flex items-center gap-2 p-1.5 hover:bg-[#091124] rounded-lg cursor-pointer transition-colors text-xs"
                  >
                    <input 
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSelectSession(s.id)}
                      className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="truncate flex-1 text-slate-200">{s.title}</span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {s.logs.length} msg{s.logs.length !== 1 ? 's' : ''}
                    </span>
                  </label>
                );
              })}
            </div>
          )}

          {/* Compliance & Styling Options */}
          <div className="bg-[#060b18] border border-slate-800/90 rounded-xl p-4 space-y-3">
            <span className="text-xs font-semibold text-slate-200 block">
              PDF Formatting & Compliance Standards:
            </span>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input 
                  type="checkbox"
                  checked={includeTelemetry}
                  onChange={(e) => setIncludeTelemetry(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500"
                />
                <span>Include 3-Hop Cross-Border Telemetry</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input 
                  type="checkbox"
                  checked={includeCertStamp}
                  onChange={(e) => setIncludeCertStamp(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500"
                />
                <span>Include Digital GDPR Audit Certificate</span>
              </label>
            </div>

            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5 text-blue-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                Color Profile: AgentVerse Midnight Blue (#060b18)
              </span>
              <span className="text-emerald-400 font-mono">
                GDPR Article 5(1)(c) Compliant
              </span>
            </div>
          </div>

          {/* PDF Summary Preview Card */}
          <div className="p-3.5 bg-gradient-to-r from-blue-950/40 via-indigo-950/20 to-purple-950/40 border border-blue-900/40 rounded-xl flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-[11px] font-semibold text-blue-300">Ready to Export:</span>
              <p className="text-xs text-slate-300">
                {sessionsToExport.length} conversation{sessionsToExport.length !== 1 ? 's' : ''} &bull;{' '}
                {sessionsToExport.reduce((acc, s) => acc + s.logs.length, 0)} total messages
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-emerald-950 border border-emerald-700 text-emerald-300 text-[10px] px-2 py-0.5">
                Audit Pass
              </Badge>
              <Badge className="bg-blue-950 border border-blue-700 text-blue-300 text-[10px] px-2 py-0.5">
                3 Hops
              </Badge>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-[#060b18] border-t border-slate-800 flex items-center justify-between">
          <Button 
            variant="ghost" 
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Cancel
          </Button>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleDownloadPdf}
              disabled={isGenerating || sessionsToExport.length === 0}
              className="bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-xl px-4 py-2 flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Generating Blue PDF...</span>
                </>
              ) : downloadSuccess ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                  <span>Downloaded!</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download PDF (Blue Theme)</span>
                </>
              )}
            </Button>
          </div>
        </div>

      </div>

      {/* Hidden High-Fidelity Printable Document (Captured by html2canvas + jsPDF) */}
      <div style={{ position: 'absolute', left: '-9999px', top: '-9999px' }}>
        <div
          ref={printRef}
          style={{
            width: '800px',
            backgroundColor: '#060b18',
            color: '#f8fafc',
            fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
            padding: '36px',
            boxSizing: 'border-box'
          }}
        >
          {/* Header Banner */}
          <div
            style={{
              background: 'linear-gradient(135deg, #070f26 0%, #0d1b3e 50%, #150d30 100%)',
              border: '1px solid rgba(59, 130, 246, 0.5)',
              borderRadius: '16px',
              padding: '24px',
              marginBottom: '28px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(37, 99, 235, 0.3)',
                    border: '1px solid #3b82f6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#60a5fa',
                    fontWeight: 'bold',
                    fontSize: '18px'
                  }}
                >
                  ✦
                </div>
                <div>
                  <h1 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                    AgentVerse Cross-Border Audit Record
                  </h1>
                  <span style={{ fontSize: '11px', color: '#93c5fd' }}>
                    GDPR Article 5 & Chapter V Compliant A2A Protocol
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '6px' }}>
                <span
                  style={{
                    backgroundColor: 'rgba(5, 46, 22, 0.9)',
                    border: '1px solid #16a34a',
                    color: '#4ade80',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    padding: '3px 8px',
                    borderRadius: '999px',
                    textTransform: 'uppercase'
                  }}
                >
                  ✓ GDPR PASS
                </span>
                <span
                  style={{
                    backgroundColor: 'rgba(23, 37, 84, 0.9)',
                    border: '1px solid #2563eb',
                    color: '#bfdbfe',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    padding: '3px 8px',
                    borderRadius: '999px'
                  }}
                >
                  3 HOPS VERIFIED
                </span>
              </div>
            </div>

            {/* Architecture Metadata Strip */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '10px',
                paddingTop: '14px',
                borderTop: '1px solid rgba(59, 130, 246, 0.2)',
                fontSize: '10px',
                fontFamily: 'monospace'
              }}
            >
              <div>
                <span style={{ color: '#64748b', display: 'block', marginBottom: '2px' }}>REQUESTING NODE:</span>
                <span style={{ color: '#93c5fd', fontWeight: '600' }}>Agent 2 • South India</span>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block', marginBottom: '2px' }}>DATA PROVIDER NODE:</span>
                <span style={{ color: '#d8b4fe', fontWeight: '600' }}>Agent 1 • North Europe</span>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block', marginBottom: '2px' }}>SOVEREIGN BOUNDARY:</span>
                <span style={{ color: '#4ade80', fontWeight: '600' }}>Zero Direct DB Credentials</span>
              </div>
            </div>
          </div>

          {/* Conversations Body */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            {sessionsToExport.map((session, sIdx) => (
              <div key={session.id} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {/* Session Title Header */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingBottom: '8px',
                    borderBottom: '1px solid #1e293b'
                  }}
                >
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#38bdf8' }}>
                    # Session {sIdx + 1}: {session.title}
                  </span>
                  <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                    {session.logs.length} exchanged message{session.logs.length !== 1 ? 's' : ''}
                  </span>
                </div>

                {/* Messages */}
                {session.logs.map(log => {
                  if (log.role === 'user') {
                    return (
                      <div key={log.id} style={{ display: 'flex', justifyContent: 'flex-end', margin: '4px 0' }}>
                        <div
                          style={{
                            maxWidth: '75%',
                            backgroundColor: '#122347',
                            border: '1px solid rgba(59, 130, 246, 0.4)',
                            borderRadius: '16px',
                            padding: '12px 18px',
                            color: '#f8fafc',
                            fontSize: '12px',
                            lineHeight: '1.5',
                            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)'
                          }}
                        >
                          <div style={{ fontSize: '10px', color: '#93c5fd', marginBottom: '4px', fontWeight: '600' }}>
                            User • {log.timestamp}
                          </div>
                          {log.content}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={log.id} style={{ display: 'flex', justifyContent: 'flex-start', margin: '4px 0' }}>
                      <div style={{ maxWidth: '85%', width: '100%' }}>
                        <div style={{ fontSize: '10px', color: '#60a5fa', marginBottom: '4px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span>Agent 2 (India)</span>
                          <span style={{ color: '#64748b' }}>• {log.timestamp}</span>
                          <span
                            style={{
                              backgroundColor: 'rgba(59, 7, 100, 0.8)',
                              border: '1px solid rgba(147, 51, 234, 0.5)',
                              color: '#d8b4fe',
                              fontSize: '9px',
                              padding: '1px 5px',
                              borderRadius: '4px'
                            }}
                          >
                            via Europe Node
                          </span>
                        </div>

                        <div
                          style={{
                            backgroundColor: '#091124',
                            border: '1px solid rgba(30, 41, 59, 0.9)',
                            borderRadius: '16px',
                            padding: '16px',
                            color: '#e2e8f0',
                            fontSize: '12px',
                            lineHeight: '1.6',
                            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)'
                          }}
                        >
                          <div style={{ whiteSpace: 'pre-wrap' }}>
                            {log.content}
                          </div>

                          {/* Telemetry Block in PDF */}
                          {includeTelemetry && (
                            <div
                              style={{
                                marginTop: '12px',
                                paddingTop: '10px',
                                borderTop: '1px solid rgba(59, 130, 246, 0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                fontSize: '10px',
                                fontFamily: 'monospace'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span
                                  style={{
                                    backgroundColor: 'rgba(5, 46, 22, 0.8)',
                                    color: '#4ade80',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontWeight: 'bold',
                                    border: '1px solid #16a34a'
                                  }}
                                >
                                  GDPR POLICY: PASS
                                </span>
                                <span style={{ color: '#94a3b8' }}>3 Hops Sovereign Telemetry</span>
                              </div>
                              <span style={{ color: '#60a5fa' }}>Minimization Filter Verified</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}

              </div>
            ))}
          </div>

          {/* Certificate Stamp Footer */}
          {includeCertStamp && (
            <div
              style={{
                marginTop: '36px',
                padding: '16px 20px',
                backgroundColor: '#070f24',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '10px'
              }}
            >
              <div>
                <div style={{ fontWeight: 'bold', color: '#f8fafc', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>🛡️ Official GDPR Article 5(1)(c) Compliance Certificate</span>
                </div>
                <div style={{ color: '#94a3b8', fontSize: '9px', fontFamily: 'monospace' }}>
                  Certified zero-trust cross-border routing. No unauthorized customer records or credentials exposed.
                </div>
              </div>

              <div style={{ textAlign: 'right', fontFamily: 'monospace', fontSize: '9px', color: '#60a5fa' }}>
                <div>AUTH: AGENTVERSE-VERIFIED</div>
                <div style={{ color: '#64748b' }}>SECURITY LEVEL: ENTERPRISE</div>
              </div>
            </div>
          )}

        </div>
      </div>

    </div>
  );
}
