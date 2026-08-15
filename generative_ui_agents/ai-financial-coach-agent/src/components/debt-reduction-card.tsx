"use client";

import { DebtReduction, PayoffPlan } from "@/lib/types";
import { useState } from "react";

type Props = { plan: DebtReduction };

export function DebtReductionCard({ plan }: Props) {
  const [tab, setTab] = useState<"avalanche" | "snowball" | "compare">(
    "avalanche",
  );
  const a = plan.payoff_plans?.avalanche;
  const s = plan.payoff_plans?.snowball;

  if (!plan.debts?.length) {
    return (
      <div className="bg-white rounded-3xl shadow-2xl p-6 max-w-3xl w-full mx-auto">
        <h3 className="text-xl font-bold text-gray-900">💳 Debt Reduction</h3>
        <p className="text-sm text-gray-500 mt-1">
          You have no debts to plan around. Keep it that way! 🎉
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl shadow-2xl p-6 max-w-3xl w-full mx-auto">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">💳 Debt Reduction</h3>
        <p className="text-sm text-gray-500">
          Two strategies to get to debt-free.
        </p>
      </div>

      <div className="rounded-2xl bg-gradient-to-r from-rose-500 to-pink-600 p-5 text-white mb-5">
        <div className="text-sm opacity-90">Total Debt</div>
        <div className="text-3xl font-bold font-mono">
          ${plan.total_debt.toLocaleString()}
        </div>
      </div>

      {/* Debt list */}
      <div className="mb-5">
        <h4 className="font-semibold text-gray-800 mb-3">📋 Your Debts</h4>
        <div className="space-y-2">
          {plan.debts.map((d, i) => (
            <div
              key={i}
              className="grid grid-cols-12 gap-2 items-center bg-gray-50 rounded-lg px-3 py-2"
            >
              <span className="col-span-4 text-sm font-medium text-gray-800">
                {d.name}
              </span>
              <span className="col-span-3 text-sm font-mono text-gray-900 text-right">
                ${d.amount.toLocaleString()}
              </span>
              <span className="col-span-2 text-xs font-mono text-amber-600 text-right">
                {d.interest_rate}%
              </span>
              <span className="col-span-3 text-xs font-mono text-gray-500 text-right">
                {d.min_payment ? `$${d.min_payment}/mo min` : "—"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-xl p-1">
        {(["avalanche", "snowball", "compare"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            {t === "avalanche"
              ? "🏔️ Avalanche"
              : t === "snowball"
                ? "❄️ Snowball"
                : "⚖️ Compare"}
          </button>
        ))}
      </div>

      {tab === "avalanche" && a && (
        <PayoffPanel
          plan={a}
          title="Avalanche — highest interest first"
          subtitle="Mathematically minimizes total interest."
          accent="from-orange-500 to-red-600"
        />
      )}
      {tab === "snowball" && s && (
        <PayoffPanel
          plan={s}
          title="Snowball — smallest balance first"
          subtitle="Builds momentum with quick wins."
          accent="from-cyan-500 to-blue-600"
        />
      )}
      {tab === "compare" && a && s && <CompareView a={a} s={s} />}

      {plan.recommendations?.length ? (
        <>
          <div className="h-px bg-gray-100 my-5" />
          <h4 className="font-semibold text-gray-800 mb-3">
            💡 Recommendations
          </h4>
          <div className="space-y-3">
            {plan.recommendations.map((rec, i) => (
              <div
                key={i}
                className="rounded-xl bg-amber-50 border border-amber-100 p-4"
              >
                <div className="text-sm font-semibold text-amber-900">
                  {rec.title}
                </div>
                <p className="text-sm text-gray-800 mt-1 leading-relaxed">
                  {rec.description}
                </p>
                {rec.impact && (
                  <p className="text-xs text-amber-700 mt-2 italic">
                    {rec.impact}
                  </p>
                )}
              </div>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

function PayoffPanel({
  plan,
  title,
  subtitle,
  accent,
}: {
  plan: PayoffPlan;
  title: string;
  subtitle: string;
  accent: string;
}) {
  const years = Math.floor(plan.months_to_payoff / 12);
  const months = plan.months_to_payoff % 12;
  return (
    <div className={`rounded-2xl bg-gradient-to-br ${accent} p-5 text-white`}>
      <div className="font-semibold">{title}</div>
      <div className="text-xs opacity-80 mb-4">{subtitle}</div>
      <div className="grid grid-cols-3 gap-3">
        <Stat
          label="Total interest"
          value={`$${plan.total_interest.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
        />
        <Stat
          label="Time to debt-free"
          value={
            years > 0
              ? `${years}y ${months}m`
              : `${plan.months_to_payoff} mo`
          }
        />
        <Stat
          label="Suggested / mo"
          value={
            plan.monthly_payment
              ? `$${plan.monthly_payment.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
              : "—"
          }
        />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white/15 backdrop-blur rounded-lg px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide opacity-80">
        {label}
      </div>
      <div className="text-lg font-bold font-mono">{value}</div>
    </div>
  );
}

function CompareView({ a, s }: { a: PayoffPlan; s: PayoffPlan }) {
  const max = Math.max(a.total_interest, s.total_interest);
  const better = a.total_interest <= s.total_interest ? "avalanche" : "snowball";
  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-gray-50 p-4">
        <div className="text-xs text-gray-500 mb-2">Total interest paid</div>
        <Bar label="Avalanche" value={a.total_interest} max={max} color="#f97316" />
        <Bar label="Snowball" value={s.total_interest} max={max} color="#06b6d4" />
      </div>
      <div className="rounded-xl bg-gray-50 p-4">
        <div className="text-xs text-gray-500 mb-2">Months to debt-free</div>
        <Bar
          label="Avalanche"
          value={a.months_to_payoff}
          max={Math.max(a.months_to_payoff, s.months_to_payoff)}
          color="#f97316"
          suffix=" mo"
          format={(v) => v.toFixed(0)}
        />
        <Bar
          label="Snowball"
          value={s.months_to_payoff}
          max={Math.max(a.months_to_payoff, s.months_to_payoff)}
          color="#06b6d4"
          suffix=" mo"
          format={(v) => v.toFixed(0)}
        />
      </div>
      <div className="text-sm text-gray-700 px-1">
        On these numbers,{" "}
        <span className="font-semibold capitalize">{better}</span> wins on total
        interest.
      </div>
    </div>
  );
}

function Bar({
  label,
  value,
  max,
  color,
  suffix = "",
  format = (v: number) =>
    `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
  suffix?: string;
  format?: (v: number) => string;
}) {
  return (
    <div className="flex items-center gap-3 mb-2 last:mb-0">
      <span className="text-xs font-medium text-gray-600 w-20">{label}</span>
      <div className="flex-1 h-5 bg-white rounded-md overflow-hidden border border-gray-100">
        <div
          className="h-full transition-all"
          style={{
            width: `${max ? (value / max) * 100 : 0}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <span className="text-sm font-mono font-semibold text-gray-800 w-24 text-right">
        {format(value)}
        {suffix}
      </span>
    </div>
  );
}
