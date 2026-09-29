import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import { FemaTestCase } from '../types';

interface PolicyChecksCardProps {
  testCase: FemaTestCase;
  isReverseRoute?: boolean;
}

export const PolicyChecksCard: React.FC<PolicyChecksCardProps> = ({
  testCase,
  isReverseRoute = false
}) => {
  const isAuthPassed = testCase.authorization;
  const isDocsPassed = testCase.supporting_documentation;
  const isEligibilityPassed = testCase.eligibility === 'VERIFIED';
  const isValidationComplete = testCase.policy_violations.length === 0;

  const sourceCountry = isReverseRoute ? testCase.destination_country : testCase.source_country;
  const destCountry = isReverseRoute ? testCase.source_country : testCase.destination_country;
  const txnType = isReverseRoute ? 'Inward Remittance (FEMA Inbound)' : 'Outward Remittance (FEMA LRS)';

  const checks = [
    {
      id: 'source_dest',
      title: 'Source and destination identified',
      detail: `${sourceCountry} → ${destCountry}`,
      status: 'pass' as const
    },
    {
      id: 'txn_type',
      title: 'Transaction type identified',
      detail: txnType,
      status: 'pass' as const
    },
    {
      id: 'auth',
      title: isAuthPassed ? 'Authorization verified' : 'Authorization missing',
      detail: isReverseRoute
        ? (isAuthPassed ? 'Inward remittance purpose code & bank clearance verified' : 'Inbound remittance authorization missing')
        : (isAuthPassed ? 'LRS compliance / bank authorization recorded' : 'Form A2 / authorized dealer clearance absent'),
      status: isAuthPassed ? ('pass' as const) : ('fail' as const)
    },
    {
      id: 'docs',
      title: isDocsPassed ? 'Supporting documentation attached' : 'Supporting documentation missing',
      detail: isDocsPassed ? 'Invoice / declaration verified' : 'No documentary proof submitted for remittance',
      status: isDocsPassed ? ('pass' as const) : ('fail' as const)
    },
    {
      id: 'eligibility',
      title: isEligibilityPassed ? 'Party eligibility verified' : 'Party eligibility not verified',
      detail: isEligibilityPassed ? 'Entities KYC & sanctions clear' : 'Foreign entity identity & sanction check incomplete',
      status: isEligibilityPassed ? ('pass' as const) : ('fail' as const)
    },
    {
      id: 'validation',
      title: isValidationComplete ? 'Required validation complete' : 'Required validation incomplete',
      detail: isValidationComplete ? 'All guardrails satisfied for transfer' : 'Mandatory FEMA policy gates failed',
      status: isValidationComplete ? ('pass' as const) : ('fail' as const)
    }
  ];

  return (
    <div className="rounded-2xl border border-slate-800/90 bg-[#060b18] p-4 sm:p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3.5">
        <span className="text-[11px] font-mono tracking-[0.18em] text-slate-300 uppercase font-semibold">
          POLICY CHECKS
        </span>
        <span className="text-[11px] font-mono text-blue-400">
          {isReverseRoute ? 'Inbound FEMA' : 'Outbound FEMA'}
        </span>
      </div>

      {/* Checks List */}
      <div className="space-y-2 font-mono text-xs">
        {checks.map((check) => {
          const isPass = check.status === 'pass';
          return (
            <div
              key={check.id}
              className={`p-2.5 rounded-xl border flex items-start gap-2.5 transition-colors ${
                isPass
                  ? 'bg-[#091124] border-slate-800 text-slate-200'
                  : 'bg-amber-950/20 border-amber-500/30 text-amber-200 shadow-[0_0_10px_-2px_rgba(245,158,11,0.08)]'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isPass ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 animate-pulse" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className={`font-medium truncate ${isPass ? 'text-slate-200' : 'text-amber-200 font-semibold'}`}>
                    {check.title}
                  </span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded uppercase tracking-wider shrink-0 ml-1.5 font-bold ${
                      isPass
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/20'
                        : 'bg-amber-900/60 text-amber-300 border border-amber-500/30'
                    }`}
                  >
                    {isPass ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                  {check.detail}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
