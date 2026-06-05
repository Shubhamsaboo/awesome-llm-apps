"use client";

import { useState, useRef, useEffect } from "react";
import { useHumanInTheLoop } from "@copilotkit/react-core/v2";
import { useAgent } from "@copilotkit/react-core/v2";
import { z } from "zod";

export function useMutationConfirmation() {
  useHumanInTheLoop(
    {
      name: "confirm_mutation",
      description:
        "Present a proposed data mutation to the user for approval. Shows the SQL diff and waits for the user to approve or reject before proceeding.",
      parameters: z.object({
        mutation_id: z.string().describe("The ID of the mutation to confirm"),
        description: z
          .string()
          .describe("Human-readable description of the mutation"),
      }),
      render: ({ status, respond, args }) => {
        return (
          <MutationApprovalCard
            status={status}
            respond={respond}
            mutationId={args?.mutation_id}
            description={args?.description}
          />
        );
      },
    },
    [],
  );
}

function MutationApprovalCard({
  status,
  respond,
  mutationId,
  description,
}: {
  status: string;
  respond?: (result: unknown) => void;
  mutationId?: string;
  description?: string;
}) {
  const { agent } = useAgent();
  const [decision, setDecision] = useState<"pending" | "approved" | "rejected">(
    "pending",
  );

  const mutation = agent.state?.pending_mutation;
  const mutationRef = useRef(mutation);
  useEffect(() => {
    if (mutation) mutationRef.current = mutation;
  }, [mutation]);

  const display = mutation || mutationRef.current;

  const isWaiting = status === "executing" && decision === "pending";
  const borderColor =
    decision === "approved"
      ? "border-green-500/50"
      : decision === "rejected"
        ? "border-red-500/50"
        : "border-amber-500/50";
  const bgColor =
    decision === "approved"
      ? "bg-green-500/5"
      : decision === "rejected"
        ? "bg-red-500/5"
        : "bg-amber-500/5";

  return (
    <div className={`rounded-lg border-2 ${borderColor} ${bgColor} p-4 my-2`}>
      <div className="flex items-center gap-2 mb-3">
        {decision === "pending" && (
          <div className="h-2.5 w-2.5 rounded-full bg-amber-500 animate-pulse" />
        )}
        {decision === "approved" && (
          <div className="h-2.5 w-2.5 rounded-full bg-green-500" />
        )}
        {decision === "rejected" && (
          <div className="h-2.5 w-2.5 rounded-full bg-red-500" />
        )}
        <span className="text-sm font-semibold text-[var(--foreground)]">
          {decision === "approved"
            ? "Write Approved"
            : decision === "rejected"
              ? "Write Rejected"
              : "Confirm Write"}
        </span>
        {(mutationId || display?.mutation_id) && (
          <span className="text-[10px] font-mono text-[var(--muted-foreground)] bg-[var(--muted)] px-1.5 py-0.5 rounded">
            {mutationId || display?.mutation_id}
          </span>
        )}
      </div>

      <p className="text-sm text-[var(--muted-foreground)] mb-3">
        {description || display?.description || "Reviewing proposed changes..."}
      </p>

      {display?.changes && (
        <div className="space-y-1.5 mb-3">
          {display.changes.map(
            (
              change: {
                column: string;
                old_value: unknown;
                new_value: unknown;
              },
              i: number,
            ) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs font-mono bg-[var(--muted)] rounded-md px-3 py-2"
              >
                <span className="text-[var(--muted-foreground)] font-medium min-w-[80px]">
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
            ),
          )}
        </div>
      )}

      {display?.sql && (
        <div className="p-2.5 bg-[var(--muted)] rounded-md text-[11px] font-mono text-[var(--muted-foreground)] mb-3 overflow-x-auto leading-relaxed">
          {display.sql}
        </div>
      )}

      {isWaiting && respond ? (
        <div className="flex gap-2">
          <button
            onClick={() => {
              setDecision("approved");
              respond({
                approved: true,
                mutation_id: mutationId || display?.mutation_id,
              });
            }}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md bg-green-600 hover:bg-green-700 text-white transition-colors cursor-pointer"
          >
            Approve
          </button>
          <button
            onClick={() => {
              setDecision("rejected");
              respond({ approved: false });
            }}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md bg-red-600 hover:bg-red-700 text-white transition-colors cursor-pointer"
          >
            Reject
          </button>
        </div>
      ) : decision === "approved" ? (
        <div className="text-sm text-green-500 font-medium flex items-center gap-1.5">
          <span>&#10003;</span> Approved — executing write.
        </div>
      ) : decision === "rejected" ? (
        <div className="text-sm text-red-500 font-medium flex items-center gap-1.5">
          <span>&#10007;</span> Rejected — write cancelled.
        </div>
      ) : (
        <div className="text-xs text-[var(--muted-foreground)]">
          Waiting for mutation details...
        </div>
      )}
    </div>
  );
}
