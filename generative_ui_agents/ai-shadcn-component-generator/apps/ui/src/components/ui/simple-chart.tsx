import * as React from "react";
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

type ChartType = "bar" | "line" | "area";

function SimpleChart({
  type = "bar",
  labels,
  values,
  label,
  color,
}: {
  type?: ChartType;
  labels: string[];
  values: number[];
  label?: string;
  color?: string;
}) {
  const displayLabel = label || "value";
  const chartColor = color || "var(--sunshine-yellow)";

  const data = labels.map((l, i) => ({
    category: l,
    series: values[i] ?? 0,
  }));

  const config: ChartConfig = {
    series: {
      label: displayLabel,
      color: chartColor,
    },
  };

  const sharedProps = {
    data,
    margin: { top: 8, right: 8, bottom: 0, left: -16 },
  };

  return (
    <ChartContainer config={config} className="min-h-[200px] w-full">
      {type === "bar" ? (
        <BarChart {...sharedProps}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="category" tickLine={false} axisLine={false} tickMargin={8} />
          <YAxis tickLine={false} axisLine={false} tickMargin={8} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="series" fill="var(--color-series)" radius={4} />
        </BarChart>
      ) : type === "line" ? (
        <LineChart {...sharedProps}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="category" tickLine={false} axisLine={false} tickMargin={8} />
          <YAxis tickLine={false} axisLine={false} tickMargin={8} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line
            type="monotone"
            dataKey="series"
            stroke="var(--color-series)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      ) : (
        <AreaChart {...sharedProps}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="category" tickLine={false} axisLine={false} tickMargin={8} />
          <YAxis tickLine={false} axisLine={false} tickMargin={8} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Area
            type="monotone"
            dataKey="series"
            fill="var(--color-series)"
            fillOpacity={0.3}
            stroke="var(--color-series)"
            strokeWidth={2}
          />
        </AreaChart>
      )}
    </ChartContainer>
  );
}

export { SimpleChart };
export type { ChartType };
