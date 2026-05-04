import { z } from "zod";
import { CHART_COLORS } from "./config";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

export const PieChartProps = z.object({
  title: z.string().describe("Chart title"),
  description: z.string().describe("Brief description or subtitle"),
  data: z.array(
    z.object({
      label: z.string(),
      value: z.number(),
    }),
  ),
});

type PieChartProps = z.infer<typeof PieChartProps>;

/** Custom SVG donut chart built with <circle> + stroke-dasharray. */
function DonutChart({
  data,
  size = 240,
  strokeWidth = 40,
}: {
  data: { label: string; value: number }[];
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  const total = data.reduce((sum, d) => sum + (Number(d.value) || 0), 0);

  // Calculate each slice's arc length and starting position
  let accumulated = 0;
  const slices = data.map((item, index) => {
    const val = Number(item.value) || 0;
    const ratio = total > 0 ? val / total : 0;
    const arc = ratio * circumference;
    const startAt = accumulated;
    accumulated += arc;
    return {
      ...item,
      arc,
      gap: circumference - arc,
      // Negative dashoffset shifts the dash forward (clockwise) to the correct position
      dashoffset: -startAt,
      color: CHART_COLORS[index % CHART_COLORS.length],
    };
  });

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${size} ${size}`}
      className="block mx-auto"
      style={{ maxWidth: size, transform: "scaleX(-1)" }}
    >
      {/* Background ring */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke="var(--secondary)"
        strokeWidth={strokeWidth}
      />
      {/* Data slices */}
      {slices.map((slice, i) => (
        <circle
          key={i}
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={slice.color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${slice.arc} ${slice.gap}`}
          strokeDashoffset={slice.dashoffset}
          strokeLinecap="butt"
          transform={`rotate(-90 ${center} ${center})`}
        />
      ))}
    </svg>
  );
}

export function PieChart({ title, description, data }: PieChartProps) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card className="max-w-lg mx-auto my-4">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--muted-foreground)] text-center py-8 text-sm">
            No data available
          </p>
        </CardContent>
      </Card>
    );
  }

  const total = data.reduce((sum, d) => sum + (Number(d.value) || 0), 0);

  return (
    <Card className="max-w-lg mx-auto my-4 overflow-hidden">
      <CardHeader className="pb-0">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <DonutChart data={data} />

        {/* Legend */}
        <div className="space-y-2 pt-4">
          {data.map((item, index) => {
            const val = Number(item.value) || 0;
            const pct = total > 0 ? ((val / total) * 100).toFixed(0) : 0;
            return (
              <div
                key={index}
                className="flex items-center gap-3 text-sm transition-opacity duration-300 ease-out"
                style={{ opacity: 1 }}
              >
                <span
                  className="inline-block h-3 w-3 rounded-full shrink-0"
                  style={{
                    backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
                  }}
                />
                <span className="flex-1 text-[var(--foreground)] truncate">
                  {item.label}
                </span>
                <span className="text-[var(--muted-foreground)] tabular-nums">
                  {val.toLocaleString()}
                </span>
                <span className="text-[var(--muted-foreground)] text-sm w-10 text-right tabular-nums">
                  {pct}%
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
