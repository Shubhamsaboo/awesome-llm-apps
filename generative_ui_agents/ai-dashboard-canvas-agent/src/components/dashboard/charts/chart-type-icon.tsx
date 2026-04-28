import {
  BarChart3,
  ChartLine,
  PieChart as PieChartIcon,
  LayoutDashboard,
} from "lucide-react";
import type { ChartSpec } from "@/lib/types";

export function ChartTypeIcon({ spec }: { spec: ChartSpec }) {
  if (spec.type === "line") return <ChartLine className="size-4" />;
  if (spec.type === "bar") return <BarChart3 className="size-4" />;
  if (spec.type === "pie") return <PieChartIcon className="size-4" />;
  return <LayoutDashboard className="size-4" />;
}
