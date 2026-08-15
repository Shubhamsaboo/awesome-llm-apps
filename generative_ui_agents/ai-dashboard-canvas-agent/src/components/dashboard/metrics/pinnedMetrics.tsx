import { Button } from "@/components/ui/button";
import { CardContent } from "@/components/ui/card";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { AgentSetState, AgentState, type Metric } from "@/lib/types";
import { RenderFunctionStatus } from "@copilotkit/react-core";
import {
  Pin,
  TrendingUp,
  Trash2,
  TrendingDown,
  DollarSign,
  Users,
  Pencil,
} from "lucide-react";
import { useState } from "react";

function MetricIcon({ name }: { name?: Metric["icon"] }) {
  switch (name) {
    case "users":
      return <Users className="size-4" />;
    case "mrr":
      return <DollarSign className="size-4" />;
    case "conversion":
      return <TrendingUp className="size-4" />;
    case "churn":
      return <TrendingDown className="size-4" />;
    default:
      return <Pin className="size-4" />;
  }
}

interface PinnedMetricCardProps {
  pinnedMetric: Metric;
  setState: AgentSetState<AgentState>;
  onHumanInput?: (shouldProceed: boolean) => void;
  status?: RenderFunctionStatus;
}

export const PinnedMetricCard = ({
  pinnedMetric,
  setState,
  onHumanInput,
  status,
}: PinnedMetricCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  return (
    <>
      <Card key={pinnedMetric.id} className="group relative">
        {!status && (
          <div className="absolute right-2 top-2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              className="text-muted-foreground hover:text-foreground"
              onClick={() => setIsEditing(true)}
              title="Edit metric"
            >
              <Pencil className="size-4" />
            </button>
            <button
              className="text-muted-foreground hover:text-foreground"
              onClick={() =>
                setState((state) => ({
                  title: state?.title ?? "Dashboard",
                  charts: state?.charts ?? [],
                  pinnedMetrics: (state?.pinnedMetrics ?? []).filter(
                    (x: Metric) => x.id !== pinnedMetric.id,
                  ),
                }))
              }
              title="Remove metric"
            >
              <Trash2 className="size-4" />
            </button>
          </div>
        )}
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <CardTitle className="inline-flex items-center gap-2 text-sm">
            <MetricIcon name={pinnedMetric.icon} />
            {pinnedMetric.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-primary truncate">
            {pinnedMetric.value}
          </div>
          {pinnedMetric.hint && (
            <p className="text-muted-foreground text-sm mt-1">
              {pinnedMetric.hint}
            </p>
          )}
        </CardContent>
      </Card>
      {isEditing && (
        <MetricEditModal
          metric={pinnedMetric}
          onCancel={() => setIsEditing(false)}
          onSave={(next) => {
            setState((state) => ({
              title: state?.title ?? "Dashboard",
              charts: state?.charts ?? [],
              pinnedMetrics: (state?.pinnedMetrics ?? []).map((m: Metric) =>
                m.id === next.id ? next : m,
              ),
            }));
            setIsEditing(false);
          }}
        />
      )}
      {status !== "complete" && onHumanInput && (
        <div className="flex justify-end gap-2 py-4">
          <Button variant="outline" onClick={() => onHumanInput(false)}>
            Cancel
          </Button>
          <Button onClick={() => onHumanInput(true)}>Add</Button>
        </div>
      )}
    </>
  );
};

function MetricEditModal({
  metric,
  onCancel,
  onSave,
}: {
  metric: Metric;
  onCancel: () => void;
  onSave: (next: Metric) => void;
}) {
  const [title, setTitle] = useState(metric.title);
  const [value, setValue] = useState(metric.value);
  const [hint, setHint] = useState(metric.hint ?? "");
  const [icon, setIcon] = useState<Metric["icon"]>(metric.icon ?? "custom");

  const save = () => {
    const safeIcon =
      icon === "users" ||
      icon === "mrr" ||
      icon === "conversion" ||
      icon === "churn" ||
      icon === "custom"
        ? icon
        : "custom";
    onSave({
      ...metric,
      title,
      value,
      hint: hint || undefined,
      icon: safeIcon,
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-card text-card-foreground w-full max-w-md rounded-lg shadow-lg border">
        <div className="p-4 border-b font-medium">Edit Metric</div>
        <div className="p-4 space-y-3">
          <div>
            <label className="block text-sm mb-1">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border rounded px-2 py-1 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Value</label>
            <input
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-full border rounded px-2 py-1 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Hint</label>
            <input
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              className="w-full border rounded px-2 py-1 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Icon</label>
            <select
              value={icon}
              onChange={(e) => setIcon(e.target.value as Metric["icon"])}
              className="w-full border rounded px-2 py-1 bg-background"
            >
              <option value="users">Users</option>
              <option value="mrr">MRR</option>
              <option value="conversion">Conversion</option>
              <option value="churn">Churn</option>
              <option value="custom">Custom</option>
            </select>
          </div>
        </div>
        <div className="p-4 border-t flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={save}>Save</Button>
        </div>
      </div>
    </div>
  );
}
