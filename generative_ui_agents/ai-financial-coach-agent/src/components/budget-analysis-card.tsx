"use client";

import { BudgetAnalysis } from "@/lib/types";

const PALETTE = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#84cc16",
  "#f97316",
];

type Props = { analysis: BudgetAnalysis };

export function BudgetAnalysisCard({ analysis }: Props) {
  const income = analysis.monthly_income ?? 0;
  const expenses = analysis.total_expenses ?? 0;
  const surplus = income - expenses;
  const cats = (analysis.spending_categories ?? []).filter((c) => c.amount > 0);

  return (
    <Card title="💰 Budget Analysis" subtitle="Where your money is going">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DonutChart categories={cats} total={expenses} />
        <div className="space-y-3">
          <Stat label="Monthly Income" value={income} positive />
          <Stat label="Monthly Expenses" value={expenses} negative />
          <Stat
            label={surplus >= 0 ? "Monthly Surplus" : "Monthly Deficit"}
            value={Math.abs(surplus)}
            positive={surplus >= 0}
            negative={surplus < 0}
            highlight
          />
        </div>
      </div>

      <Divider />

      <h4 className="font-semibold text-gray-800 mb-3">📋 Category Breakdown</h4>
      <div className="space-y-2">
        {cats.map((c, i) => {
          const pct = c.percentage ?? (expenses ? (c.amount / expenses) * 100 : 0);
          return (
            <div key={c.category} className="flex items-center gap-3">
              <span
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: PALETTE[i % PALETTE.length] }}
              />
              <span className="text-sm font-medium text-gray-800 w-40">
                {c.category}
              </span>
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${Math.min(pct, 100)}%`,
                    backgroundColor: PALETTE[i % PALETTE.length],
                  }}
                />
              </div>
              <span className="text-xs font-mono text-gray-500 w-14 text-right">
                {pct.toFixed(1)}%
              </span>
              <span className="text-sm font-mono font-semibold text-gray-900 w-20 text-right">
                ${c.amount.toLocaleString()}
              </span>
            </div>
          );
        })}
      </div>

      {analysis.recommendations?.length ? (
        <>
          <Divider />
          <h4 className="font-semibold text-gray-800 mb-3">
            💡 Recommendations
          </h4>
          <div className="space-y-3">
            {analysis.recommendations.map((rec, i) => (
              <div
                key={i}
                className="rounded-xl bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-100 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">
                      {rec.category}
                    </div>
                    <p className="text-sm text-gray-800 mt-1 leading-relaxed">
                      {rec.recommendation}
                    </p>
                  </div>
                  {rec.potential_savings ? (
                    <div className="text-right shrink-0">
                      <div className="text-xs text-gray-500">Save / mo</div>
                      <div className="text-lg font-bold text-emerald-600">
                        ${rec.potential_savings.toLocaleString()}
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </Card>
  );
}

function DonutChart({
  categories,
  total,
}: {
  categories: { category: string; amount: number }[];
  total: number;
}) {
  if (!categories.length || !total) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-gray-400">
        No spending data yet
      </div>
    );
  }
  const radius = 70;
  const stroke = 22;
  const c = 2 * Math.PI * radius;
  let cumulative = 0;
  const segments = categories.map((cat, i) => {
    const portion = cat.amount / total;
    const dash = portion * c;
    const offset = -cumulative * c;
    cumulative += portion;
    return (
      <circle
        key={cat.category}
        r={radius}
        cx={100}
        cy={100}
        fill="transparent"
        stroke={PALETTE[i % PALETTE.length]}
        strokeWidth={stroke}
        strokeDasharray={`${dash} ${c - dash}`}
        strokeDashoffset={offset}
        transform="rotate(-90 100 100)"
      />
    );
  });
  return (
    <div className="flex items-center justify-center">
      <div className="relative">
        <svg width={200} height={200} viewBox="0 0 200 200">
          {segments}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="text-xs text-gray-500">Total</div>
          <div className="text-xl font-bold text-gray-900">
            ${total.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  positive,
  negative,
  highlight,
}: {
  label: string;
  value: number;
  positive?: boolean;
  negative?: boolean;
  highlight?: boolean;
}) {
  const color = positive
    ? "text-emerald-600"
    : negative
      ? "text-red-500"
      : "text-gray-900";
  return (
    <div
      className={`rounded-xl px-4 py-3 ${
        highlight ? "bg-gradient-to-r from-gray-900 to-gray-700 text-white" : "bg-gray-50"
      }`}
    >
      <div className={`text-xs ${highlight ? "text-gray-300" : "text-gray-500"}`}>
        {label}
      </div>
      <div
        className={`text-2xl font-bold font-mono ${highlight ? "text-white" : color}`}
      >
        {negative && !highlight ? "-" : ""}${value.toLocaleString()}
      </div>
    </div>
  );
}

function Card({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-3xl shadow-2xl p-6 max-w-3xl w-full mx-auto">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function Divider() {
  return <div className="h-px bg-gray-100 my-5" />;
}
