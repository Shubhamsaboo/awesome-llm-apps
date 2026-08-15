import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2, Pencil } from "lucide-react";
import type {
  Chart,
  ChartSpec,
  ChartDataMap,
  LineChartSpec,
  BarChartSpec,
  PieChartSpec,
} from "@/lib/types";
import { ChartRenderer } from "./chart-renderer";
import { ChartTypeIcon } from "./chart-type-icon";

interface ChartGridProps {
  charts: Chart[];
  onRemoveChart: (index: number) => void;
  onEditChart: (index: number, newSpec: ChartSpec) => void;
  chartData?: ChartDataMap;
}

export function ChartGrid({
  charts,
  onRemoveChart,
  onEditChart,
}: ChartGridProps) {
  const [editIndex, setEditIndex] = useState<number | null>(null);
  const [draft, setDraft] = useState<ChartSpec | null>(null);

  const startEdit = (index: number) => {
    setEditIndex(index);
    setDraft(charts[index]);
  };

  const handleSave = (newSpec: ChartSpec) => {
    if (editIndex !== null) {
      onEditChart(editIndex, newSpec);
    }
    setEditIndex(null);
    setDraft(null);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {charts &&
        Array.isArray(charts) &&
        charts?.map((c, i) => (
          <Card key={i} className="group">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base inline-flex items-center gap-2">
                <ChartTypeIcon spec={c} />
                {"title" in c ? c.title : "Untitled"}
              </CardTitle>
              <div className="flex items-center gap-2">
                <button
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground transition-opacity"
                  onClick={() => startEdit(i)}
                  title="Edit chart"
                >
                  <Pencil className="size-4" />
                </button>
                <button
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground transition-opacity"
                  onClick={() => onRemoveChart(i)}
                  title="Remove chart"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <ChartRenderer spec={c} data={c.data} />
            </CardContent>
          </Card>
        ))}

      {editIndex !== null && draft && (
        <ChartEditModal
          spec={draft}
          onCancel={() => {
            setEditIndex(null);
            setDraft(null);
          }}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

function ChartEditModal({
  spec,
  onCancel,
  onSave,
}: {
  spec: ChartSpec;
  onCancel: () => void;
  onSave: (next: ChartSpec) => void;
}) {
  const [title, setTitle] = useState<string>("title" in spec ? spec.title : "");
  const [x, setX] = useState<string>("x" in spec ? spec.x : "");
  const [y, setY] = useState<string>("y" in spec ? spec.y : "");
  const [steps, setSteps] = useState<string>(
    "steps" in spec && Array.isArray(spec.steps) ? spec.steps.join(", ") : "",
  );

  const buildSpec = (): ChartSpec => {
    const type = spec.type; // Keep the original type
    if (type === "line") return { type, title, x, y } as LineChartSpec;
    if (type === "bar") return { type, title, x, y } as BarChartSpec;
    return { type, title, x: x || "category", y: y || "value" } as PieChartSpec;
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-card text-card-foreground w-full max-w-md rounded-lg shadow-lg border">
        <div className="p-4 border-b font-medium">Edit Chart</div>
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
            <label className="block text-sm mb-1">X</label>
            <input
              value={x}
              onChange={(e) => setX(e.target.value)}
              className="w-full border rounded px-2 py-1 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Y</label>
            <input
              value={y}
              onChange={(e) => setY(e.target.value)}
              className="w-full border rounded px-2 py-1 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">
              Steps (comma separated)
            </label>
            <input
              value={steps}
              onChange={(e) => setSteps(e.target.value)}
              className="w-full border rounded px-2 py-1 bg-background"
            />
          </div>
        </div>
        <div className="p-4 border-t flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={() => onSave(buildSpec())}>Save</Button>
        </div>
      </div>
    </div>
  );
}
