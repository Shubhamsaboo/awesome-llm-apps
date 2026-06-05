"use client";

interface PendingMutation {
  mutation_id: string;
  sql: string;
  params: unknown[];
  table: string;
  row_id: number;
  changes: { column: string; old_value: unknown; new_value: unknown }[];
  description: string;
}

export function CanvasMutationPreview({
  mutation,
}: {
  mutation: PendingMutation;
}) {
  return (
    <div className="rounded-xl border-2 border-amber-500/50 bg-amber-500/5 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="h-3 w-3 rounded-full bg-amber-500 animate-pulse" />
        <h2 className="text-lg font-semibold text-[var(--foreground)]">
          Pending Write
        </h2>
        <span className="text-xs font-mono text-[var(--muted-foreground)] bg-[var(--muted)] px-2 py-0.5 rounded">
          {mutation.mutation_id}
        </span>
      </div>

      <p className="text-sm text-[var(--muted-foreground)] mb-4">
        {mutation.description}
      </p>

      <div className="space-y-3 mb-4">
        {mutation.changes.map((change, i) => (
          <div
            key={i}
            className="flex items-center gap-3 text-sm font-mono bg-[var(--muted)] rounded-lg px-4 py-2"
          >
            <span className="text-[var(--muted-foreground)] font-medium">
              {change.column}
            </span>
            <span className="text-red-400 line-through">
              {String(change.old_value)}
            </span>
            <span className="text-[var(--muted-foreground)]">&rarr;</span>
            <span className="text-green-400 font-semibold">
              {String(change.new_value)}
            </span>
          </div>
        ))}
      </div>

      <div className="p-3 bg-[var(--muted)] rounded-lg text-xs font-mono text-[var(--muted-foreground)] mb-4 overflow-x-auto">
        {mutation.sql}
      </div>

      <p className="text-sm text-[var(--muted-foreground)]">
        Type <strong>&quot;confirm&quot;</strong> or{" "}
        <strong>&quot;reject&quot;</strong> in chat to proceed.
      </p>
    </div>
  );
}
