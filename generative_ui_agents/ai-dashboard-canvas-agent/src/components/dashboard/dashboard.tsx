import { useCoAgent } from "@copilotkit/react-core";
import { AgentState } from "@/lib/types";
import { cn } from "@/lib/utils";
import { PinnedMetrics } from "@/components/dashboard/layout/metrics";
import { Charts } from "@/components/dashboard/layout/charts";
import { useChartActions, useSearchActions } from "@/components/chat/actions";

export function MainLayout({ className }: { className?: string }) {
  const { state, setState } = useCoAgent<AgentState>({
    name: "my_agent",
  });

  // Setup tool rendering and front-end tools
  useChartActions({ state, setState });
  useSearchActions();

  return (
    <div
      className={cn("min-h-screen bg-background text-foreground", className)}
    >
      <div className="max-w-6xl mx-auto p-4 grid gap-4">
        <PinnedMetrics state={state} setState={setState} />
        <Charts state={state} setState={setState} />
      </div>
    </div>
  );
}
