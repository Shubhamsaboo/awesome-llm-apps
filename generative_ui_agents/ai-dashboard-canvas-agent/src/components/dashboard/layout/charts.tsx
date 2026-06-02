import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { ChartSpec, Chart, ChartDataMap } from "@/lib/types";
import { AgentState, AgentSetState } from "@/lib/types";
import { ChartGrid } from "@/components/dashboard/charts";

interface ChartsProps {
  state: AgentState;
  setState: AgentSetState<AgentState>;
}

export const Charts = ({ state, setState }: ChartsProps) => {
  const handleRemoveChart = (index: number) => {
    setState((prev) => {
      const charts = [...(prev?.charts ?? [])];
      charts.splice(index, 1);
      return {
        title: prev?.title ?? "Dashboard",
        charts,
        pinnedMetrics: prev?.pinnedMetrics ?? [],
      } as AgentState;
    });
  };

  const handleEditChart = (index: number, newSpec: ChartSpec) => {
    setState((prev) => {
      const charts = [...(prev?.charts ?? [])];
      // Preserve the data when editing
      const existingData = charts[index]?.data ?? [];
      charts[index] = { ...newSpec, data: existingData } as Chart;
      return {
        title: prev?.title ?? "Dashboard",
        charts,
        pinnedMetrics: prev?.pinnedMetrics ?? [],
      } as AgentState;
    });
  };

  const handleAddChart = () => {
    const newChart: Chart = {
      type: "line",
      title: "New Chart",
      x: "x",
      y: "y",
      data: [],
    } as Chart;
    setState((prev) => ({
      title: prev?.title ?? "Dashboard",
      charts: [...(prev?.charts ?? []), newChart],
      pinnedMetrics: prev?.pinnedMetrics ?? [],
    }));
  };

  return (
    <Card className="shadow-none border-none pt-4 m-0 bg-transparent">
      <CardHeader className="flex flex-row items-center justify-between p-0 m-0">
        <div className="flex items-center gap-2">
          <CardTitle className="text-xl">Your charts</CardTitle>
        </div>
        <Button
          size="sm"
          variant="suggestion"
          onClick={handleAddChart}
          title="Add chart"
        >
          <Plus className="size-4 mr-1" /> Add Chart
        </Button>
      </CardHeader>
      <CardContent className="p-0 m-0">
        {!state?.charts?.length && (
          <p className="text-sm italic">
            No dashboard yet. Describe what you want in chat (eg, &quot;funnel
            of signups and revenue line chart&quot;).
          </p>
        )}
        {state?.charts?.length > 0 && (
          <ChartGrid
            charts={state.charts}
            chartData={
              (state as AgentState & { chartData?: ChartDataMap }).chartData
            }
            onRemoveChart={handleRemoveChart}
            onEditChart={handleEditChart}
          />
        )}
      </CardContent>
    </Card>
  );
};
