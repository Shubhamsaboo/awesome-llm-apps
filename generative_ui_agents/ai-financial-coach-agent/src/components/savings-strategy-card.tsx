"use client";

import { SavingsStrategy } from "@/lib/types";

type Props = { strategy: SavingsStrategy };

export function SavingsStrategyCard({ strategy }: Props) {
  const ef = strategy.emergency_fund;
  const efProgress = ef.recommended_amount
    ? Math.min((ef.current_amount ?? 0) / ef.recommended_amount, 1)
    : 0;

  return (
    <div className="bg-white rounded-3xl shadow-2xl p-6 max-w-3xl w-full mx-auto">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">📈 Savings Strategy</h3>
        <p className="text-sm text-gray-500">
          Personalized plan for emergency fund, savings, and automation.
        </p>
      </div>

      {/* Emergency Fund */}
      <div className="rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 p-5 mb-5">
        <div className="flex items-baseline justify-between mb-2">
          <h4 className="font-semibold text-emerald-900">🛟 Emergency Fund</h4>
          <span className="text-xs uppercase tracking-wide font-bold text-emerald-700">
            {ef.current_status}
          </span>
        </div>
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-3xl font-bold text-gray-900 font-mono">
            ${(ef.current_amount ?? 0).toLocaleString()}
          </span>
          <span className="text-sm text-gray-500">
            of ${ef.recommended_amount.toLocaleString()} recommended
          </span>
        </div>
        <div className="h-3 rounded-full bg-emerald-100 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all"
            style={{ width: `${efProgress * 100}%` }}
          />
        </div>
        <div className="text-xs text-gray-600 mt-2">
          {(efProgress * 100).toFixed(0)}% funded
        </div>
      </div>

      {/* Recommendations */}
      {strategy.recommendations?.length ? (
        <div className="mb-5">
          <h4 className="font-semibold text-gray-800 mb-3">
            💵 Monthly Savings Allocations
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {strategy.recommendations.map((r, i) => (
              <div
                key={i}
                className="rounded-xl bg-gray-50 border border-gray-100 p-4"
              >
                <div className="flex items-baseline justify-between mb-1">
                  <span className="text-sm font-semibold text-gray-800">
                    {r.category}
                  </span>
                  <span className="text-lg font-bold text-emerald-600 font-mono">
                    ${r.amount.toLocaleString()}
                  </span>
                </div>
                {r.rationale && (
                  <p className="text-xs text-gray-600 leading-relaxed">
                    {r.rationale}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Automation */}
      {strategy.automation_techniques?.length ? (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3">
            ⚙️ Automation Techniques
          </h4>
          <ul className="space-y-2">
            {strategy.automation_techniques.map((t, i) => (
              <li
                key={i}
                className="flex gap-3 rounded-lg bg-indigo-50/50 border border-indigo-100 p-3"
              >
                <span className="text-indigo-500 text-lg">→</span>
                <div>
                  <div className="text-sm font-semibold text-indigo-900">
                    {t.name}
                  </div>
                  <div className="text-xs text-gray-700 mt-0.5 leading-relaxed">
                    {t.description}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
