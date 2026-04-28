export type LineChartSpec = {
  type: "line";
  title: string;
  x: string;
  y: string;
};
export type BarChartSpec = { type: "bar"; title: string; x: string; y: string };
export type PieChartSpec = { type: "pie"; title: string; x: string; y: string };
export type ChartSpec = LineChartSpec | BarChartSpec | PieChartSpec;

// Data records supplied by the agent for charts
export type ChartDataRecord = Record<string, string | number>;
export type ChartDataMap = Record<string, ChartDataRecord[]>; // keyed by chart title

export type Metric = {
  id: string;
  title: string;
  value: string;
  hint?: string;
  icon?: "users" | "mrr" | "conversion" | "churn" | "custom";
};

export type Chart = ChartSpec & {
  data: ChartDataRecord[];
};

export type AgentState = {
  title: string;
  charts: Chart[];
  pinnedMetrics: Metric[];
};

export type AgentSetState<T extends AgentState> = (
  newState: T | ((prevState: T | undefined) => T),
) => void;

export const initialState: AgentState = {
  title: "Dashboard",
  charts: [
    {
      type: "line",
      title: "Sales by day",
      x: "x",
      y: "y",
      data: [
        { x: "2024-01-01", y: 100 },
        { x: "2024-01-02", y: 200 },
        { x: "2024-01-03", y: 300 },
      ],
    },
    {
      type: "bar",
      title: "Sales by product",
      x: "x",
      y: "y",
      data: [
        { x: "Smartphone", y: 100 },
        { x: "Tablet", y: 200 },
        { x: "Laptop", y: 300 },
      ],
    },
  ],
  pinnedMetrics: [
    {
      id: "1",
      title: "Total sales",
      value: "1000",
      hint: "Total sales for the last 30 days",
      icon: "mrr",
    },
    {
      id: "2",
      title: "Best selling product",
      value: "Laptop",
      hint: "Total sales for the last 30 days",
      icon: "conversion",
    },
  ],
};
