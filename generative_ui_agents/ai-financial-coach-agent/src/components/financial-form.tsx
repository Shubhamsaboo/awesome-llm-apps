"use client";

import {
  DEFAULT_FINANCIAL_DATA,
  EXPENSE_CATEGORIES,
  FinancialData,
  Debt,
} from "@/lib/types";
import { useMemo } from "react";

type Props = {
  data: FinancialData;
  onChange: (next: FinancialData) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
};

export function FinancialForm({
  data,
  onChange,
  onAnalyze,
  isAnalyzing,
}: Props) {
  const totalExpenses = useMemo(
    () => Object.values(data.manual_expenses ?? {}).reduce((a, b) => a + (b || 0), 0),
    [data.manual_expenses],
  );

  const totalDebt = useMemo(
    () => (data.debts ?? []).reduce((a, d) => a + (d.amount || 0), 0),
    [data.debts],
  );

  const set = (patch: Partial<FinancialData>) =>
    onChange({ ...DEFAULT_FINANCIAL_DATA, ...data, ...patch });

  const setExpense = (key: string, value: number) =>
    set({ manual_expenses: { ...data.manual_expenses, [key]: value } });

  const updateDebt = (idx: number, patch: Partial<Debt>) => {
    const next = [...(data.debts ?? [])];
    next[idx] = { ...next[idx], ...patch };
    set({ debts: next });
  };

  const addDebt = () =>
    set({
      debts: [
        ...(data.debts ?? []),
        {
          name: `Debt ${data.debts.length + 1}`,
          amount: 1000,
          interest_rate: 5,
          min_payment: 50,
        },
      ],
    });

  const removeDebt = (idx: number) =>
    set({ debts: (data.debts ?? []).filter((_, i) => i !== idx) });

  return (
    <div className="bg-white/95 backdrop-blur rounded-3xl shadow-2xl p-8 max-w-3xl w-full mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            💼 Your Financial Picture
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Fill in your details, then ask the coach to analyze.
          </p>
        </div>
      </div>

      {/* Income & dependants */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Field label="Monthly Income ($)" emoji="💵" wide>
          <NumberInput
            value={data.monthly_income}
            onChange={(v) => set({ monthly_income: v })}
            step={100}
          />
        </Field>
        <Field label="Dependants" emoji="👨‍👩‍👧">
          <NumberInput
            value={data.dependants}
            onChange={(v) => set({ dependants: Math.max(0, Math.floor(v)) })}
            step={1}
          />
        </Field>
      </section>

      {/* Expenses */}
      <section className="mb-6">
        <SectionHeader emoji="💳" title="Monthly Expenses" total={totalExpenses} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {EXPENSE_CATEGORIES.map((c) => (
            <Field key={c.key} label={c.label} emoji={c.emoji}>
              <NumberInput
                value={data.manual_expenses?.[c.key] ?? 0}
                onChange={(v) => setExpense(c.key, v)}
                step={50}
              />
            </Field>
          ))}
        </div>
      </section>

      {/* Debts */}
      <section className="mb-6">
        <SectionHeader emoji="🏦" title="Debts" total={totalDebt} />
        <div className="space-y-3">
          {(data.debts ?? []).map((debt, idx) => (
            <div
              key={idx}
              className="grid grid-cols-12 gap-2 bg-gray-50 rounded-xl p-3 items-center"
            >
              <input
                className="col-span-3 px-3 py-2 rounded-lg bg-white border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-offset-1"
                style={{ "--tw-ring-color": "#14b8a6" } as React.CSSProperties}
                value={debt.name}
                onChange={(e) => updateDebt(idx, { name: e.target.value })}
                placeholder="Debt name"
              />
              <NumberInput
                className="col-span-3"
                value={debt.amount}
                onChange={(v) => updateDebt(idx, { amount: v })}
                step={100}
                prefix="$"
              />
              <NumberInput
                className="col-span-2"
                value={debt.interest_rate}
                onChange={(v) => updateDebt(idx, { interest_rate: v })}
                step={0.1}
                suffix="%"
              />
              <NumberInput
                className="col-span-3"
                value={debt.min_payment ?? 0}
                onChange={(v) => updateDebt(idx, { min_payment: v })}
                step={10}
                prefix="$/mo"
              />
              <button
                className="col-span-1 text-gray-400 hover:text-red-500 text-xl"
                onClick={() => removeDebt(idx)}
                title="Remove debt"
              >
                ×
              </button>
            </div>
          ))}
          <button
            onClick={addDebt}
            className="text-sm font-medium px-4 py-2 rounded-lg border-2 border-dashed border-gray-300 hover:border-gray-400 text-gray-600 w-full"
          >
            + Add a debt
          </button>
        </div>
      </section>

      <button
        onClick={onAnalyze}
        disabled={isAnalyzing}
        className="w-full py-3 rounded-xl text-white font-semibold shadow-lg transition disabled:opacity-60 hover:opacity-90 bg-gradient-to-r from-emerald-500 to-teal-500"
      >
        {isAnalyzing ? "🤖 Analyzing..." : "🔄 Analyze My Finances"}
      </button>
    </div>
  );
}

function SectionHeader({
  emoji,
  title,
  total,
}: {
  emoji: string;
  title: string;
  total: number;
}) {
  return (
    <div className="flex items-baseline justify-between mb-3">
      <h3 className="text-lg font-semibold text-gray-800">
        {emoji} {title}
      </h3>
      <span className="text-sm text-gray-500">
        Total: <span className="font-mono font-medium text-gray-900">${total.toLocaleString()}</span>
      </span>
    </div>
  );
}

function Field({
  label,
  emoji,
  children,
  wide,
}: {
  label: string;
  emoji?: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <label className={`block ${wide ? "md:col-span-2" : ""}`}>
      <span className="block text-xs font-medium text-gray-600 mb-1">
        {emoji} {label}
      </span>
      {children}
    </label>
  );
}

function NumberInput({
  value,
  onChange,
  step = 1,
  prefix,
  suffix,
  className = "",
}: {
  value: number;
  onChange: (v: number) => void;
  step?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}) {
  return (
    <div className={`relative ${className}`}>
      {prefix && (
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 pointer-events-none">
          {prefix}
        </span>
      )}
      <input
        type="number"
        step={step}
        min={0}
        value={Number.isFinite(value) ? value : 0}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className={`w-full px-3 py-2 rounded-lg bg-white border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 ${
          prefix ? "pl-12" : ""
        } ${suffix ? "pr-8" : ""}`}
      />
      {suffix && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 pointer-events-none">
          {suffix}
        </span>
      )}
    </div>
  );
}
