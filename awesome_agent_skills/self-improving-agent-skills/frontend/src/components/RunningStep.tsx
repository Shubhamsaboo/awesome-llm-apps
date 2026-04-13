"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Loader2, StopCircle } from "lucide-react";

interface RunningStepProps {
  sessionId: string;
  apiKey: string;
  scenarios: any[];
  evals: any[];
  onComplete: (result: any) => void;
}

interface Experiment {
  experiment_id: number;
  description: string;
  status: string;
  score: number;
  max_score: number;
  pass_rate: number;
  per_eval: any[];
}

export default function RunningStep({
  sessionId,
  apiKey,
  scenarios,
  evals,
  onComplete,
}: RunningStepProps) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [currentScore, setCurrentScore] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [currentExperiment, setCurrentExperiment] = useState<string>("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (!started) {
      setStarted(true);
      startOptimization();
    }
  }, []);

  const startOptimization = async () => {
    setIsRunning(true);
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8891";

    try {
      // Start the optimization
      const startResponse = await fetch(
        `${API_BASE}/api/start/${sessionId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            gemini_api_key: apiKey,
            max_rounds: 20,
          }),
        }
      );

      if (!startResponse.ok) {
        const err = await startResponse.json().catch(() => ({}));
        if (!err.detail?.includes("already running")) {
          throw new Error(err.detail || "Failed to start optimization");
        }
      }

      // Poll for status every 3 seconds
      const poll = async () => {
        let lastExpCount = 0;
        while (true) {
          await new Promise((r) => setTimeout(r, 3000));

          try {
            const res = await fetch(`${API_BASE}/api/status/${sessionId}`);
            if (!res.ok) continue;
            const data = await res.json();

            // Update experiments if new ones arrived
            if (data.experiments && data.experiments.length > lastExpCount) {
              const newExps = data.experiments;
              setExperiments(newExps);
              const latest = newExps[newExps.length - 1];
              setCurrentScore(latest.pass_rate);
              setCurrentExperiment(
                latest.status === "baseline"
                  ? "Baseline complete"
                  : `Experiment ${latest.experiment_id}: ${latest.status}`
              );
              lastExpCount = newExps.length;
            }

            // Check if complete
            if (data.status === "complete" && data.final_result) {
              setIsRunning(false);
              onComplete(data.final_result);
              return;
            }

            if (data.status === "error") {
              setIsRunning(false);
              alert(`Error: ${data.error || "Unknown error"}`);
              return;
            }

            if (data.status === "stopped") {
              setIsRunning(false);
              return;
            }
          } catch {
            // Network error, keep polling
          }
        }
      };

      poll();
    } catch (error: any) {
      alert(error.message || "Failed to start optimization.");
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    try {
      const API_BASE2 = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8891";
      await fetch(`${API_BASE2}/api/stop/${sessionId}`, {
        method: "POST",
      });
      setIsRunning(false);
    } catch (error) {
      alert("Failed to stop optimization");
    }
  };

  const chartData = experiments.map((exp) => ({
    experiment: exp.experiment_id === 0 ? "Base" : exp.experiment_id.toString(),
    passRate: exp.pass_rate,
    status: exp.status,
  }));

  const evalBreakdown = evals.map((evalItem) => {
    const latestExperiment = experiments[experiments.length - 1];
    if (!latestExperiment) {
      return { ...evalItem, passed: 0, total: 0, passRate: 0 };
    }

    const evalResult = latestExperiment.per_eval?.find(
      (pe: any) => pe.eval_id === evalItem.id
    );

    return {
      ...evalItem,
      passed: evalResult?.passed || 0,
      total: evalResult?.total || 0,
      passRate: evalResult?.pass_rate || 0,
    };
  });

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="glass rounded-2xl p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-2">
              {currentScore.toFixed(1)}
              <span className="text-lg text-zinc-500">%</span>
            </h2>
            <p className="text-zinc-400">{currentExperiment}</p>
          </div>

          {isRunning && (
            <button
              onClick={handleStop}
              className="px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl transition-all flex items-center gap-2"
            >
              <StopCircle className="w-5 h-5" />
              Stop Optimization
            </button>
          )}
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="experiment"
              stroke="#71717a"
              style={{ fontSize: "12px" }}
            />
            <YAxis
              stroke="#71717a"
              style={{ fontSize: "12px" }}
              domain={[0, 100]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #27272a",
                borderRadius: "8px",
              }}
            />
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Line
              type="monotone"
              dataKey="passRate"
              stroke="#8b5cf6"
              strokeWidth={3}
              dot={(props: any) => {
                const { cx, cy, payload, index } = props;
                const color =
                  payload.status === "baseline"
                    ? "#3b82f6"
                    : payload.status === "keep"
                    ? "#22c55e"
                    : "#ef4444";
                return <circle key={`dot-${index}`} cx={cx} cy={cy} r={5} fill={color} />;
              }}
              fill="url(#colorGradient)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass rounded-2xl p-8">
          <h3 className="text-xl font-bold mb-6">Experiment Log</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {experiments.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-zinc-500">
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
            ) : (
              experiments.map((exp) => (
                <div
                  key={exp.experiment_id}
                  className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span
                      className={`
                      px-3 py-1 rounded-full text-xs font-medium
                      ${
                        exp.status === "baseline"
                          ? "bg-blue-500/20 text-blue-400"
                          : exp.status === "keep"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-red-500/20 text-red-400"
                      }
                    `}
                    >
                      {exp.status === "baseline"
                        ? "Baseline"
                        : exp.status === "keep"
                        ? "Keep ✓"
                        : "Discard ✗"}
                    </span>
                    <span className="text-lg font-bold text-violet-400">
                      {exp.pass_rate}%
                    </span>
                  </div>
                  <p className="text-sm text-zinc-400">
                    {exp.experiment_id === 0
                      ? "Initial baseline"
                      : exp.description}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="glass rounded-2xl p-8">
          <h3 className="text-xl font-bold mb-6">Evaluation Breakdown</h3>
          <div className="space-y-4">
            {evalBreakdown.map((evalItem) => (
              <div key={evalItem.id}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{evalItem.name}</span>
                  <span className="text-sm text-zinc-400">
                    {evalItem.passed}/{evalItem.total}
                  </span>
                </div>
                <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full gradient-bg transition-all duration-500"
                    style={{ width: `${evalItem.passRate}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
