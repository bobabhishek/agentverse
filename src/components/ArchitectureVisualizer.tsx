'use client';

import { 
  User, 
  Bot, 
  Database, 
  Eye, 
  ShieldAlert, 
  ArrowRight, 
  ArrowDown, 
  ArrowLeft,
  ArrowUp,
  Lock,
  Radio
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ArchitectureVisualizerProps {
  orientation: 'vertical' | 'horizontal';
}

export default function ArchitectureVisualizer({ orientation }: ArchitectureVisualizerProps) {
  if (orientation === 'vertical') {
    return (
      <div className="w-full max-w-2xl mx-auto py-6 px-4 space-y-4">
        {/* Step 1: User */}
        <div className="flex flex-col items-center">
          <div className="w-full bg-[#0a1226] border-2 border-slate-700/80 rounded-2xl p-4 shadow-lg flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-100">User / Operator</h4>
                <p className="text-xs text-slate-400">Initiates customer data request</p>
              </div>
            </div>
            <Badge className="bg-slate-800 text-slate-300 border-slate-700 text-[10px]">Step 1 & 6</Badge>
          </div>

          {/* Arrow 1: User to Agent 2 */}
          <div className="flex flex-col items-center my-1 text-blue-400">
            <div className="h-6 w-0.5 bg-blue-500/60" />
            <div className="bg-[#0b132b] px-3 py-1 rounded-full border border-blue-800/80 text-[11px] font-semibold text-blue-300 flex items-center gap-1 shadow-sm">
              <ArrowDown className="w-3.5 h-3.5" />
              <span>1. Customer Query</span>
            </div>
            <div className="h-6 w-0.5 bg-blue-500/60" />
          </div>

          {/* Step 2: Agent 2 (India) */}
          <div className="w-full bg-gradient-to-r from-[#071330] to-[#0c1c44] border-2 border-blue-500/80 rounded-2xl p-4 shadow-xl shadow-blue-950/40 relative">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-blue-950 border border-blue-500/70 flex items-center justify-center text-blue-300 shadow-md">
                  <Bot className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-base text-white">Agent 2 &bull; India Node</h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-900/60 text-blue-200 border border-blue-700/50">
                      Requesting Agent
                    </span>
                  </div>
                  <p className="text-xs text-blue-200/80 mt-0.5">
                    Receives user prompt &bull; <strong className="text-rose-300">No direct database access</strong>
                  </p>
                </div>
              </div>
              <Badge className="bg-blue-900/80 text-blue-200 border-blue-600 text-xs">Step 2</Badge>
            </div>
          </div>

          {/* Arrow 2: Cross-Border A2A Request & Response */}
          <div className="flex flex-col items-center my-1 text-purple-400">
            <div className="h-6 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-purple-600" />
            <div className="flex flex-col sm:flex-row items-center gap-2">
              <div className="bg-[#1a0f35] px-3 py-1 rounded-full border border-purple-700 text-[11px] font-semibold text-purple-200 flex items-center gap-1 shadow-sm">
                <ArrowDown className="w-3.5 h-3.5 text-purple-400" />
                <span>2. A2A Request across border</span>
              </div>
              <div className="bg-[#1a0f35] px-3 py-1 rounded-full border border-purple-700 text-[11px] font-semibold text-purple-200 flex items-center gap-1 shadow-sm">
                <ArrowUp className="w-3.5 h-3.5 text-emerald-400" />
                <span>5. A2A Response (Refusal / Disclosure)</span>
              </div>
            </div>
            <div className="h-6 w-0.5 bg-gradient-to-b from-purple-600 to-purple-500" />
          </div>

          {/* Step 3: Agent 1 (Europe) */}
          <div className="w-full bg-gradient-to-r from-[#170a2c] to-[#250d44] border-2 border-purple-500/80 rounded-2xl p-4 shadow-xl shadow-purple-950/40 relative">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-purple-950 border border-purple-500/70 flex items-center justify-center text-purple-300 shadow-md">
                  <Database className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-base text-white">Agent 1 &bull; Europe Node</h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-900/60 text-purple-200 border border-purple-700/50">
                      Data Owner
                    </span>
                  </div>
                  <p className="text-xs text-purple-200/80 mt-0.5">
                    Validates request &bull; Exclusive access to European customer records &bull; Enforces policy
                  </p>
                </div>
              </div>
              <Badge className="bg-purple-900/80 text-purple-200 border-purple-600 text-xs">Step 3</Badge>
            </div>
          </div>

          {/* Arrow 3: DB Query */}
          <div className="flex flex-col items-center my-1 text-cyan-400">
            <div className="h-6 w-0.5 bg-cyan-600/70" />
            <div className="bg-[#051c2c] px-3 py-1 rounded-full border border-cyan-700 text-[11px] font-semibold text-cyan-200 flex items-center gap-1 shadow-sm">
              <ArrowDown className="w-3.5 h-3.5" />
              <span>3 & 4. Query & Return Synthetic Customer Data</span>
            </div>
            <div className="h-6 w-0.5 bg-cyan-600/70" />
          </div>

          {/* Step 4: Synthetic Database */}
          <div className="w-full bg-[#061826] border-2 border-cyan-500/80 rounded-2xl p-4 shadow-lg shadow-cyan-950/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-950 border border-cyan-700 flex items-center justify-center text-cyan-300">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-cyan-100">Synthetic Customer Database</h4>
                  <p className="text-xs text-cyan-300/80">Local Europe store &bull; Strictly synthetic demo records</p>
                </div>
              </div>
              <Badge className="bg-cyan-950 text-cyan-300 border-cyan-800 text-[10px]">Isolated DB</Badge>
            </div>
          </div>

          {/* Separate Monitoring Section: GlassBox */}
          <div className="w-full mt-6 pt-5 border-t-2 border-dashed border-slate-700/80">
            <div className="bg-[#061a14] border-2 border-emerald-500/80 rounded-2xl p-4 shadow-xl shadow-emerald-950/30">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl bg-emerald-950 border border-emerald-500/70 flex items-center justify-center text-emerald-300 shadow-md">
                    <Eye className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-base text-white">GlassBox</h4>
                      <Badge className="bg-emerald-900/80 text-emerald-200 border-emerald-600 text-[10px]">
                        Independent External Monitor
                      </Badge>
                    </div>
                    <p className="text-xs text-emerald-200/80 mt-0.5">
                      Observes Agent 2 &rarr; Agent 1 interaction out-of-band &bull; Detects & flags non-compliance
                    </p>
                  </div>
                </div>

                <div className="bg-[#1f0909] border border-rose-600/80 px-3.5 py-2 rounded-xl flex items-center gap-2 text-rose-300 shrink-0">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span className="text-xs font-bold uppercase tracking-wide">Observe / Flag</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Horizontal Flow Layout
  return (
    <div className="w-full overflow-x-auto py-6 px-2">
      <div className="min-w-[780px] max-w-4xl mx-auto space-y-6">
        {/* Main Flow: User -> Agent 2 -> Agent 1 -> Synthetic DB */}
        <div className="grid grid-cols-4 gap-3 items-center">
          {/* Node 1: User */}
          <div className="bg-[#0a1226] border-2 border-slate-700/80 rounded-2xl p-4 shadow-md text-center flex flex-col items-center h-full justify-between">
            <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200 mb-2">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-100">User</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">Customer Query</p>
            </div>
            <Badge className="bg-slate-800 text-slate-300 text-[9px] mt-2">Operator</Badge>
          </div>

          {/* Node 2: Agent 2 India */}
          <div className="bg-gradient-to-b from-[#071330] to-[#0c1c44] border-2 border-blue-500 rounded-2xl p-4 shadow-xl text-center flex flex-col items-center h-full justify-between relative">
            <div className="w-10 h-10 rounded-xl bg-blue-950 border border-blue-500/70 flex items-center justify-center text-blue-300 mb-2">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-white">Agent 2 (India)</h4>
              <p className="text-[11px] text-blue-300 mt-0.5">Requesting Agent</p>
            </div>
            <span className="text-[10px] text-rose-300 font-mono mt-1 font-semibold">No direct DB access</span>
          </div>

          {/* Node 3: Agent 1 Europe */}
          <div className="bg-gradient-to-b from-[#170a2c] to-[#250d44] border-2 border-purple-500 rounded-2xl p-4 shadow-xl text-center flex flex-col items-center h-full justify-between">
            <div className="w-10 h-10 rounded-xl bg-purple-950 border border-purple-500/70 flex items-center justify-center text-purple-300 mb-2">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-white">Agent 1 (Europe)</h4>
              <p className="text-[11px] text-purple-300 mt-0.5">Data Owner</p>
            </div>
            <span className="text-[10px] text-emerald-300 font-mono mt-1 font-semibold">Local DB Access</span>
          </div>

          {/* Node 4: Synthetic DB */}
          <div className="bg-[#061826] border-2 border-cyan-500 rounded-2xl p-4 shadow-md text-center flex flex-col items-center h-full justify-between">
            <div className="w-10 h-10 rounded-xl bg-cyan-950 border border-cyan-700 flex items-center justify-center text-cyan-300 mb-2">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-cyan-100">Synthetic DB</h4>
              <p className="text-[11px] text-cyan-300 mt-0.5">Customer Records</p>
            </div>
            <Badge className="bg-cyan-950 text-cyan-300 border-cyan-800 text-[9px] mt-2">Synthetic</Badge>
          </div>
        </div>

        {/* Step Flow Bar */}
        <div className="bg-[#060b18] border border-slate-800 rounded-xl p-3 flex items-center justify-between text-xs text-slate-300 font-mono">
          <div className="flex items-center gap-1.5 text-blue-400 font-semibold">
            <span>1. User Query</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
          <div className="flex items-center gap-1.5 text-purple-400 font-semibold">
            <span>2. Cross-Border A2A Request</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
          <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
            <span>3. DB Lookup</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
          <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span>4. A2A Response & Deliver</span>
          </div>
        </div>

        {/* External GlassBox Observation Tier */}
        <div className="border-t-2 border-dashed border-slate-700/80 pt-4">
          <div className="bg-[#061a14] border-2 border-emerald-500/80 rounded-2xl p-4 flex items-center justify-between shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-950 border border-emerald-500 flex items-center justify-center text-emerald-300">
                <Eye className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-sm text-white">GlassBox</h4>
                  <Badge className="bg-emerald-900/80 text-emerald-200 border-emerald-600 text-[9px]">
                    Independent External Monitor
                  </Badge>
                </div>
                <p className="text-xs text-emerald-300/80 mt-0.5">
                  Observes A2A interaction telemetry &bull; Does not participate in communication chain
                </p>
              </div>
            </div>

            <div className="bg-[#1f0909] border border-rose-600/80 px-4 py-2 rounded-xl flex items-center gap-2 text-rose-300 shadow-md">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span className="text-xs font-bold uppercase tracking-wider">Observe / Flag</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
