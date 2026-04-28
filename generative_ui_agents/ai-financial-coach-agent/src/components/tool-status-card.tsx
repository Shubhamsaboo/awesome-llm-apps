"use client";

type Status = "inProgress" | "executing" | "complete";

type Props = {
  icon: string;
  inProgressLabel: string;
  completeLabel: string;
  status: Status;
  detail?: string;
};

export function ToolStatusCard({
  icon,
  inProgressLabel,
  completeLabel,
  status,
  detail,
}: Props) {
  const isDone = status === "complete";
  return (
    <div
      className={`my-2 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm border transition-colors ${
        isDone
          ? "bg-emerald-50 border-emerald-200 text-emerald-900"
          : "bg-slate-50 border-slate-200 text-slate-700"
      }`}
    >
      <span className="text-base leading-none">{isDone ? "✅" : icon}</span>
      <span className="font-medium">
        {isDone ? completeLabel : inProgressLabel}
      </span>
      {!isDone && (
        <span className="ml-1 inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      )}
      {isDone && detail && (
        <span className="ml-1 text-xs text-emerald-700/80">{detail}</span>
      )}
    </div>
  );
}
