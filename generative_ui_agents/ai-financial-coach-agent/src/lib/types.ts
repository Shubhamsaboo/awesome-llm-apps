// Mirrors the agent's pydantic schemas in agent/main.py.

export type SpendingCategory = {
  category: string;
  amount: number;
  percentage?: number | null;
};

export type SpendingRecommendation = {
  category: string;
  recommendation: string;
  potential_savings?: number | null;
};

export type BudgetAnalysis = {
  total_expenses: number;
  monthly_income?: number | null;
  spending_categories: SpendingCategory[];
  recommendations: SpendingRecommendation[];
};

export type EmergencyFund = {
  recommended_amount: number;
  current_amount?: number | null;
  current_status: string;
};

export type SavingsRecommendation = {
  category: string;
  amount: number;
  rationale?: string | null;
};

export type AutomationTechnique = {
  name: string;
  description: string;
};

export type SavingsStrategy = {
  emergency_fund: EmergencyFund;
  recommendations: SavingsRecommendation[];
  automation_techniques?: AutomationTechnique[] | null;
};

export type Debt = {
  name: string;
  amount: number;
  interest_rate: number;
  min_payment?: number | null;
};

export type PayoffPlan = {
  total_interest: number;
  months_to_payoff: number;
  monthly_payment?: number | null;
};

export type PayoffPlans = {
  avalanche: PayoffPlan;
  snowball: PayoffPlan;
};

export type DebtRecommendation = {
  title: string;
  description: string;
  impact?: string | null;
};

export type DebtReduction = {
  total_debt: number;
  debts: Debt[];
  payoff_plans: PayoffPlans;
  recommendations?: DebtRecommendation[] | null;
};

export type FinancialData = {
  monthly_income: number;
  dependants: number;
  manual_expenses: Record<string, number>;
  debts: Debt[];
};

export type AgentState = {
  financial_data: FinancialData;
  budget_analysis?: BudgetAnalysis;
  savings_strategy?: SavingsStrategy;
  debt_reduction?: DebtReduction;
};

export const DEFAULT_FINANCIAL_DATA: FinancialData = {
  monthly_income: 0,
  dependants: 0,
  manual_expenses: {},
  debts: [],
};

export const EXPENSE_CATEGORIES: { key: string; label: string; emoji: string }[] = [
  { key: "Housing", label: "Housing", emoji: "🏠" },
  { key: "Utilities", label: "Utilities", emoji: "🔌" },
  { key: "Food", label: "Food", emoji: "🍽️" },
  { key: "Transportation", label: "Transportation", emoji: "🚗" },
  { key: "Healthcare", label: "Healthcare", emoji: "🏥" },
  { key: "Entertainment", label: "Entertainment", emoji: "🎭" },
  { key: "Personal", label: "Personal", emoji: "👤" },
  { key: "Savings", label: "Savings", emoji: "💰" },
  { key: "Other", label: "Other", emoji: "📦" },
];
