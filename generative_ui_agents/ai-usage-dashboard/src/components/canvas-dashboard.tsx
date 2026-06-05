"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronUp, Pencil, X } from "lucide-react";
import { useAgent, useCopilotKit } from "@copilotkit/react-core/v2";

interface QueryResult {
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  result_type: string;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    Active: "bg-green-500/15 text-green-400 border-green-500/30",
    Churned: "bg-red-500/15 text-red-400 border-red-500/30",
    Trial: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    Suspended: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    Paid: "bg-green-500/15 text-green-400 border-green-500/30",
    Overdue: "bg-red-500/15 text-red-400 border-red-500/30",
    Draft: "bg-gray-500/15 text-gray-400 border-gray-500/30",
    Void: "bg-gray-500/15 text-gray-400 border-gray-500/30",
  };
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full border ${colors[status] || "bg-gray-500/15 text-gray-400 border-gray-500/30"}`}
    >
      {status}
    </span>
  );
}

function TypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    Enterprise: "bg-purple-500/15 text-purple-400",
    Scale: "bg-indigo-500/15 text-indigo-400",
    Startup: "bg-cyan-500/15 text-cyan-400",
    Free: "bg-gray-500/15 text-gray-400",
  };
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded ${colors[type] || "bg-gray-500/15 text-gray-400"}`}
    >
      {type}
    </span>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <span className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
        {label}
      </span>
      <div className="text-2xl font-bold text-[var(--foreground)] mt-1">
        {typeof value === "number"
          ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
          : value}
      </div>
    </div>
  );
}

const STATUS_COLS = ["status", "invoice_status", "account_status"];
const TYPE_COLS = ["type", "account_type"];
const MONEY_PATTERNS = ["mrr", "amount", "total", "revenue", "cost", "price"];
const READONLY_COLS = ["id", "created_at", "recorded_at"];

function isBadgeCol(col: string) {
  return STATUS_COLS.includes(col) || TYPE_COLS.includes(col);
}

function isMoneyCol(col: string) {
  return MONEY_PATTERNS.some((p) => col.toLowerCase().includes(p));
}

function EditableCell({
  value,
  column,
  rowId,
  tableName,
}: {
  value: unknown;
  column: string;
  rowId: number | null;
  tableName: string | null;
}) {
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState(String(value ?? ""));
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();
  const isReadonly = READONLY_COLS.includes(column) || !rowId || !tableName;

  if (editing && !isReadonly) {
    return (
      <div className="flex items-center gap-1">
        <input
          className="bg-[var(--muted)] border border-[var(--border)] rounded px-2 py-0.5 text-sm text-[var(--foreground)] w-full min-w-[80px] focus:outline-none focus:ring-1 focus:ring-blue-500"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && editValue !== String(value ?? "")) {
              setEditing(false);
              agent.addMessage({
                id: crypto.randomUUID(),
                role: "user",
                content: `In the ${tableName} table, set ${column} to "${editValue}" for the row with id ${rowId}.`,
              });
              copilotkit
                .runAgent({ agent })
                .catch((e) => console.error("Inline edit run failed:", e));
            }
            if (e.key === "Escape") {
              setEditing(false);
              setEditValue(String(value ?? ""));
            }
          }}
          autoFocus
        />
        <button
          onClick={() => {
            setEditing(false);
            setEditValue(String(value ?? ""));
          }}
          className="text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  if (STATUS_COLS.includes(column)) {
    return (
      <span
        className={
          isReadonly
            ? ""
            : "cursor-pointer group/cell inline-flex items-center gap-1"
        }
        onClick={(e) => {
          e.stopPropagation();
          if (!isReadonly) setEditing(true);
        }}
      >
        <StatusBadge status={String(value)} />
        {!isReadonly && (
          <Pencil className="h-3 w-3 text-[var(--muted-foreground)] opacity-0 group-hover/cell:opacity-100 transition-opacity" />
        )}
      </span>
    );
  }

  if (TYPE_COLS.includes(column)) {
    return <TypeBadge type={String(value)} />;
  }

  if (isMoneyCol(column) && typeof value === "number") {
    return (
      <span
        className={`font-mono text-[var(--foreground)] inline-flex items-center gap-1 ${!isReadonly ? "cursor-pointer hover:bg-[var(--muted)] rounded px-1 -mx-1 group/cell" : ""}`}
        onClick={(e) => {
          e.stopPropagation();
          if (!isReadonly) setEditing(true);
        }}
      >
        $
        {value.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}
        {!isReadonly && (
          <Pencil className="h-3 w-3 text-[var(--muted-foreground)] opacity-0 group-hover/cell:opacity-100 transition-opacity" />
        )}
      </span>
    );
  }

  if (value === null) {
    return (
      <span className="text-[var(--muted-foreground)] italic text-xs">—</span>
    );
  }

  return (
    <span
      className={`text-[var(--foreground)] inline-flex items-center gap-1 ${!isReadonly ? "cursor-pointer hover:bg-[var(--muted)] rounded px-1 -mx-1 group/cell" : ""}`}
      onClick={(e) => {
        e.stopPropagation();
        if (!isReadonly) setEditing(true);
      }}
    >
      {String(value)}
      {!isReadonly && (
        <Pencil className="h-3 w-3 text-[var(--muted-foreground)] opacity-0 group-hover/cell:opacity-100 transition-opacity" />
      )}
    </span>
  );
}

function DetailPanel({
  row,
  columns,
  tableName,
}: {
  row: Record<string, unknown>;
  columns: string[];
  tableName: string | null;
}) {
  const rowId = typeof row.id === "number" ? row.id : null;

  return (
    <tr>
      <td colSpan={columns.length + 1} className="p-0">
        <div className="bg-[var(--card)] border-b border-[var(--border)]">
          <div className="mx-4 my-3 p-4 rounded-lg bg-[var(--muted)]/50 border border-[var(--border)]">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3">
              {columns.map((col) => (
                <div key={col} className="space-y-0.5">
                  <span className="text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider">
                    {col.replace(/_/g, " ")}
                  </span>
                  <div className="text-sm">
                    <EditableCell
                      value={row[col]}
                      column={col}
                      rowId={rowId}
                      tableName={tableName}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </td>
    </tr>
  );
}

function guessTableName(columns: string[]): string | null {
  if (
    columns.includes("plan_id") ||
    columns.includes("api_key") ||
    columns.includes("company_name")
  )
    return "account";
  if (
    columns.includes("tokens_in") ||
    columns.includes("tokens_out") ||
    columns.includes("model")
  )
    return "usage_events";
  if (
    columns.includes("due_date") ||
    columns.includes("paid_at") ||
    columns.includes("line_items")
  )
    return "invoices";
  if (columns.includes("limit_value") || columns.includes("current_usage"))
    return "entitlements";
  if (columns.includes("threshold_pct") || columns.includes("triggered"))
    return "alerts";
  if (columns.includes("event_limit") || columns.includes("seat_limit"))
    return "plans";
  return "account";
}

export function CanvasDashboard({
  queryResult,
  expandedRow,
  setExpandedRow,
  highlightedRow,
}: {
  queryResult: QueryResult;
  expandedRow: number | null;
  setExpandedRow: (row: number | null) => void;
  highlightedRow: number | null;
}) {
  const rows = queryResult.rows;
  const columns = queryResult.columns;
  const tableName = guessTableName(columns);

  const isAggregate =
    queryResult.result_type === "aggregate" ||
    (rows.length === 1 &&
      columns.length <= 4 &&
      Object.values(rows[0]).every((v) => typeof v === "number" || v === null));

  if (isAggregate && rows.length === 1) {
    return (
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(rows[0]).map(([key, val]) => (
            <MetricCard
              key={key}
              label={key.replace(/_/g, " ")}
              value={typeof val === "number" ? val : String(val ?? "—")}
            />
          ))}
        </div>
        <SqlFooter sql={queryResult.sql} />
      </div>
    );
  }

  const isGroupedSummary =
    rows.length >= 2 &&
    rows.length <= 12 &&
    columns.length >= 2 &&
    columns.length <= 4 &&
    columns.some((c) => typeof rows[0][c] === "string") &&
    columns.some((c) => typeof rows[0][c] === "number");

  if (isGroupedSummary) {
    const labelCol =
      columns.find((c) => typeof rows[0][c] === "string") || columns[0];
    const valueCols = columns.filter(
      (c) => c !== labelCol && typeof rows[0][c] === "number",
    );

    return (
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-[var(--muted-foreground)]">
            {rows.length} group{rows.length !== 1 ? "s" : ""}
          </span>
          <SqlFooter sql={queryResult.sql} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {rows.map((row, i) => (
            <div
              key={i}
              className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 hover:bg-[var(--muted)]/40 transition-colors"
            >
              <div className="flex items-center gap-2 mb-3">
                {STATUS_COLS.includes(labelCol) ? (
                  <StatusBadge status={String(row[labelCol])} />
                ) : TYPE_COLS.includes(labelCol) ? (
                  <TypeBadge type={String(row[labelCol])} />
                ) : (
                  <span className="text-sm font-semibold text-[var(--foreground)]">
                    {String(row[labelCol])}
                  </span>
                )}
              </div>
              {valueCols.map((vc) => (
                <div key={vc} className="mt-2">
                  <span className="text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider">
                    {vc.replace(/_/g, " ")}
                  </span>
                  <div className="text-xl font-bold text-[var(--foreground)]">
                    {isMoneyCol(vc) && typeof row[vc] === "number"
                      ? `$${(row[vc] as number).toLocaleString(undefined, { maximumFractionDigits: 2 })}`
                      : typeof row[vc] === "number"
                        ? (row[vc] as number).toLocaleString(undefined, {
                            maximumFractionDigits: 2,
                          })
                        : String(row[vc])}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (queryResult.result_type === "single_row") {
    const row = rows[0];
    const rowId = typeof row.id === "number" ? row.id : null;
    return (
      <div className="p-6">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 max-w-2xl">
          <div className="grid grid-cols-2 gap-4">
            {columns.map((col) => (
              <div key={col} className="space-y-1">
                <span className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
                  {col.replace(/_/g, " ")}
                </span>
                <div className="text-sm">
                  <EditableCell
                    value={row[col]}
                    column={col}
                    rowId={rowId}
                    tableName={tableName}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-[var(--border)]">
            <SqlFooter sql={queryResult.sql} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-[var(--muted-foreground)]">
          {queryResult.row_count} row{queryResult.row_count !== 1 ? "s" : ""}
        </span>
        <SqlFooter sql={queryResult.sql} />
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] bg-[var(--muted)]">
                <th className="w-8" />
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-3 text-left font-medium text-[var(--muted-foreground)] whitespace-nowrap text-xs uppercase tracking-wide"
                  >
                    {col.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const isExpanded = expandedRow === i;
                const rowId = typeof row.id === "number" ? row.id : null;
                return (
                  <Fragment key={i}>
                    <tr
                      className={`border-b border-[var(--border)] cursor-pointer transition-colors ${highlightedRow === i ? "bg-blue-500/15 ring-1 ring-blue-500/30" : isExpanded ? "bg-[var(--muted)]/60" : "hover:bg-[var(--muted)]/40"}`}
                      onClick={() => setExpandedRow(isExpanded ? null : i)}
                    >
                      <td className="px-2 py-3 text-[var(--muted-foreground)]">
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </td>
                      {columns.map((col) => (
                        <td key={col} className="px-4 py-3 whitespace-nowrap">
                          {isBadgeCol(col) ? (
                            STATUS_COLS.includes(col) ? (
                              <StatusBadge status={String(row[col])} />
                            ) : (
                              <TypeBadge type={String(row[col])} />
                            )
                          ) : isMoneyCol(col) &&
                            typeof row[col] === "number" ? (
                            <span className="font-mono text-[var(--foreground)]">
                              $
                              {(row[col] as number).toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </span>
                          ) : row[col] === null ? (
                            <span className="text-[var(--muted-foreground)] italic text-xs">
                              —
                            </span>
                          ) : (
                            <span className="text-[var(--foreground)]">
                              {String(row[col])}
                            </span>
                          )}
                        </td>
                      ))}
                    </tr>
                    {isExpanded && (
                      <DetailPanel
                        key={`detail-${i}`}
                        row={row}
                        columns={columns}
                        tableName={tableName}
                      />
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SqlFooter({ sql }: { sql: string }) {
  return (
    <button
      className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] font-mono cursor-pointer px-2 py-1 rounded hover:bg-[var(--muted)] transition-colors"
      onClick={(e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(sql);
      }}
    >
      Copy SQL
    </button>
  );
}
