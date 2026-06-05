"use client";

import { useRenderTool } from "@copilotkit/react-core/v2";
import { useAgent } from "@copilotkit/react-core/v2";
import { z } from "zod";

export function useToolRendering() {
  useQueryDatabaseRenderer();
  useExecuteMutationRenderer();
}

function useQueryDatabaseRenderer() {
  useRenderTool(
    {
      name: "query_database",
      parameters: z.object({
        query: z.string(),
      }),
      render: ({ status, parameters }) => {
        return (
          <QueryDatabaseCard status={status} query={parameters?.query ?? ""} />
        );
      },
    },
    [],
  );
}

function QueryDatabaseCard({
  status,
  query,
}: {
  status: string;
  query: string;
}) {
  const { agent } = useAgent();
  const rowCount = agent.state?.query_result?.row_count;
  const truncated = query.length > 60 ? query.substring(0, 60) + "..." : query;

  return (
    <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)] py-1 my-1">
      <div
        className={`h-1.5 w-1.5 rounded-full shrink-0 ${
          status === "complete" ? "bg-green-500" : "bg-blue-500 animate-pulse"
        }`}
      />
      <span className="font-mono truncate">Queried: {truncated}</span>
      {status === "complete" && rowCount != null && (
        <span className="text-[var(--muted-foreground)] shrink-0">
          ({rowCount} row{rowCount !== 1 ? "s" : ""})
        </span>
      )}
    </div>
  );
}

function useExecuteMutationRenderer() {
  useRenderTool(
    {
      name: "execute_mutation",
      parameters: z.object({
        mutation_id: z.string(),
      }),
      render: ({ status, parameters }) => {
        const mutationId = parameters?.mutation_id ?? "...";
        const isComplete = status === "complete";

        return (
          <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)] py-1 my-1">
            <div
              className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                isComplete ? "bg-green-500" : "bg-blue-500 animate-pulse"
              }`}
            />
            <span>
              {isComplete ? (
                <>
                  <span className="text-green-500">&#10003;</span> Executed
                  mutation {mutationId}
                </>
              ) : (
                <>Executing mutation {mutationId}...</>
              )}
            </span>
          </div>
        );
      },
    },
    [],
  );
}
