"use client";

import { BudgetAnalysisCard } from "@/components/budget-analysis-card";
import { DebtReductionCard } from "@/components/debt-reduction-card";
import { FinancialForm } from "@/components/financial-form";
import { SavingsStrategyCard } from "@/components/savings-strategy-card";
import { ToolStatusCard } from "@/components/tool-status-card";
import { AgentState, DEFAULT_FINANCIAL_DATA, FinancialData } from "@/lib/types";
import {
  useCoAgent,
  useCopilotAction,
  useCopilotChat,
} from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { useEffect, useRef, useState } from "react";

type Tab = "profile" | "report";

export default function CopilotKitPage() {
  return (
    <main>
      <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "🪙 Financial Coach",
          initial:
            "👋 I'm your financial coach. Tell me about your finances in chat (\"my income is $8k\", \"add a $500 student loan at 5%\") or fill in the **Profile** tab — then ask for an analysis.",
        }}
        suggestions={[
          {
            title: "Update profile",
            message:
              "My monthly income is $8,000, I have 2 dependants, my rent is $2,400 and groceries are $700.",
          },
          {
            title: "Run a full review",
            message: "Run a full financial review using my current profile.",
          },
          {
            title: "Plan my debt payoff",
            message: "Just plan my debt payoff strategy.",
          },
        ]}
      >
        <MainContent />
      </CopilotSidebar>
    </main>
  );
}

function MainContent() {
  const { state, setState, running } = useCoAgent<AgentState>({
    name: "my_agent",
    initialState: {
      financial_data: DEFAULT_FINANCIAL_DATA,
    },
  });

  const { appendMessage } = useCopilotChat();

  const [tab, setTab] = useState<Tab>("profile");
  const prevRunning = useRef(false);

  // Render handlers for backend tool calls (shown inside chat).
  useCopilotAction({
    name: "update_financial_data",
    available: "remote",
    render: ({ status, result }) => (
      <ToolStatusCard
        icon="🔧"
        inProgressLabel="Updating profile…"
        completeLabel="Profile updated"
        status={status}
        detail={
          status === "complete" && Array.isArray(result?.changes)
            ? result.changes.join(" · ")
            : undefined
        }
      />
    ),
  });

  useCopilotAction({
    name: "BudgetAnalysisAgent",
    available: "remote",
    render: ({ status }) => (
      <ToolStatusCard
        icon="💰"
        inProgressLabel="Analyzing budget…"
        completeLabel="Budget analyzed"
        status={status}
      />
    ),
  });

  useCopilotAction({
    name: "SavingsStrategyAgent",
    available: "remote",
    render: ({ status }) => (
      <ToolStatusCard
        icon="📈"
        inProgressLabel="Building savings strategy…"
        completeLabel="Savings strategy ready"
        status={status}
      />
    ),
  });

  useCopilotAction({
    name: "DebtReductionAgent",
    available: "remote",
    render: ({ status }) => (
      <ToolStatusCard
        icon="💳"
        inProgressLabel="Planning debt payoff…"
        completeLabel="Debt plan ready"
        status={status}
      />
    ),
  });

  useCopilotAction({
    name: "FullAnalysisPipeline",
    available: "remote",
    render: ({ status }) => (
      <ToolStatusCard
        icon="🧮"
        inProgressLabel="Running full review (Budget → Savings → Debt)…"
        completeLabel="Full review complete"
        status={status}
      />
    ),
  });

  const financialData: FinancialData =
    state?.financial_data ?? DEFAULT_FINANCIAL_DATA;

  const hasReport =
    !!state?.budget_analysis ||
    !!state?.savings_strategy ||
    !!state?.debt_reduction;

  // Auto-switch to Report tab when an analysis run finishes.
  useEffect(() => {
    if (prevRunning.current && !running && hasReport) {
      setTab("report");
    }
    prevRunning.current = !!running;
  }, [running, hasReport]);

  const handleAnalyze = () => {
    appendMessage(
      new TextMessage({
        role: MessageRole.User,
        content:
          "Run a full financial review using my current profile (FullAnalysisPipeline).",
      }),
    );
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-emerald-950 via-teal-900 to-emerald-800">
      <div className="max-w-6xl mx-auto py-10 px-6 space-y-8">
        <header className="text-white">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            🪙 AI Financial Coach
          </h1>
          <p className="mt-2 text-white/80 max-w-2xl">
            Powered by Google ADK + CopilotKit + AG-UI. Chat with your coach to
            update your profile, then run a Budget → Savings → Debt review.
          </p>
        </header>

        <Tabs tab={tab} setTab={setTab} hasReport={hasReport} />

        {tab === "profile" && (
          <FinancialForm
            data={financialData}
            onChange={(next) =>
              setState({ ...(state ?? {}), financial_data: next })
            }
            onAnalyze={handleAnalyze}
            isAnalyzing={!!running}
          />
        )}

        {tab === "report" && (
          <div className="space-y-8">
            {state?.budget_analysis && (
              <BudgetAnalysisCard analysis={state.budget_analysis} />
            )}
            {state?.savings_strategy && (
              <SavingsStrategyCard strategy={state.savings_strategy} />
            )}
            {state?.debt_reduction && (
              <DebtReductionCard plan={state.debt_reduction} />
            )}

            {!hasReport && (
              <div className="bg-white/10 backdrop-blur rounded-3xl p-10 text-white/80 text-center max-w-3xl mx-auto">
                <div className="text-5xl mb-3">📊</div>
                <p className="text-lg">No analysis yet.</p>
                <p className="text-sm text-white/60 mt-1">
                  Fill in your profile and ask the coach for a review.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Tabs({
  tab,
  setTab,
  hasReport,
}: {
  tab: Tab;
  setTab: (t: Tab) => void;
  hasReport: boolean;
}) {
  const items: { id: Tab; label: string; badge?: string }[] = [
    { id: "profile", label: "👤 Profile" },
    {
      id: "report",
      label: "📊 Report",
      badge: hasReport ? "ready" : undefined,
    },
  ];
  return (
    <div className="inline-flex gap-1 bg-white/10 backdrop-blur rounded-2xl p-1">
      {items.map((it) => (
        <button
          key={it.id}
          onClick={() => setTab(it.id)}
          className={`px-5 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2 ${
            tab === it.id
              ? "bg-white text-emerald-950 shadow"
              : "text-white/80 hover:text-white"
          }`}
        >
          <span>{it.label}</span>
          {it.badge && (
            <span
              className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${
                tab === it.id
                  ? "bg-teal-100 text-teal-700"
                  : "bg-teal-400/30 text-teal-50"
              }`}
            >
              {it.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
