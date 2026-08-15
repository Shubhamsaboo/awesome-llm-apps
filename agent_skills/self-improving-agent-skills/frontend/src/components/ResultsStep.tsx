"use client";

import { useState } from "react";
import { Download, RotateCcw, TrendingUp, CheckCircle, XCircle } from "lucide-react";
import { diffLines, Change } from "diff";

interface ResultsStepProps {
  result: any;
  sessionId: string;
  onStartOver: () => void;
}

export default function ResultsStep({
  result,
  sessionId,
  onStartOver,
}: ResultsStepProps) {
  const [showDiff, setShowDiff] = useState(false);

  const handleDownload = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8891"}/api/download/${sessionId}`
      );

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "improved_skill.zip";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert("Download failed. Please try again.");
    }
  };

  const improvementPercent =
    result.final_score - result.baseline_score;

  const topChanges = result.changelog
    ?.filter((c: any) => c.status === "keep")
    .slice(0, 5) || [];

  const diff = diffLines(
    result.original_skill_md || "",
    result.improved_skill_md || ""
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="glass rounded-2xl p-12 text-center">
        <div className="inline-flex items-center gap-6 mb-6">
          <div>
            <div className="text-5xl font-bold text-zinc-400">
              {result.baseline_score.toFixed(0)}%
            </div>
            <div className="text-sm text-zinc-500 mt-1">Baseline</div>
          </div>

          <TrendingUp className="w-12 h-12 text-violet-500" />

          <div>
            <div className="text-5xl font-bold gradient-text">
              {result.final_score.toFixed(0)}%
            </div>
            <div className="text-sm text-zinc-500 mt-1">Final</div>
          </div>
        </div>

        <div className="text-3xl font-bold text-green-400 mb-2">
          +{improvementPercent.toFixed(1)}%
        </div>
        <p className="text-zinc-400">Improvement achieved</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold mb-2">
            {result.experiments_run}
          </div>
          <div className="text-sm text-zinc-400">Experiments Run</div>
        </div>

        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-green-400 mb-2">
            {result.kept}
          </div>
          <div className="text-sm text-zinc-400">Changes Kept</div>
        </div>

        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-red-400 mb-2">
            {result.discarded}
          </div>
          <div className="text-sm text-zinc-400">Changes Discarded</div>
        </div>
      </div>

      {topChanges.length > 0 && (
        <div className="glass rounded-2xl p-8">
          <h3 className="text-2xl font-bold mb-6">Top Changes</h3>
          <div className="space-y-4">
            {topChanges.map((change: any, idx: number) => (
              <div
                key={idx}
                className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium mb-1">{change.description}</div>
                    <div className="text-sm text-zinc-400">
                      {change.reasoning}
                    </div>
                    <div className="text-xs text-zinc-500 mt-2">
                      Score: {change.score_before} → {change.score_after}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass rounded-2xl p-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold">Skill Changes</h3>
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            {showDiff ? "Hide" : "Show"} Diff
          </button>
        </div>

        {showDiff && (
          <div className="bg-zinc-900 rounded-lg p-6 overflow-x-auto">
            <div className="font-mono text-sm space-y-1">
              {diff.map((part: Change, idx: number) => {
                const lines = part.value.split("\n").filter((l) => l.trim());
                return lines.map((line, lineIdx) => (
                  <div
                    key={`${idx}-${lineIdx}`}
                    className={`
                      px-2 py-1
                      ${part.added ? "bg-green-500/20 text-green-400" : ""}
                      ${part.removed ? "bg-red-500/20 text-red-400" : ""}
                      ${!part.added && !part.removed ? "text-zinc-400" : ""}
                    `}
                  >
                    {part.added && "+ "}
                    {part.removed && "- "}
                    {!part.added && !part.removed && "  "}
                    {line}
                  </div>
                ));
              })}
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <button
          onClick={handleDownload}
          className="flex-1 py-4 gradient-bg rounded-xl font-semibold hover:scale-105 transition-all flex items-center justify-center gap-2"
        >
          <Download className="w-5 h-5" />
          Download Improved Skill
        </button>

        <button
          onClick={onStartOver}
          className="flex-1 py-4 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
        >
          <RotateCcw className="w-5 h-5" />
          Start Over
        </button>
      </div>
    </div>
  );
}
