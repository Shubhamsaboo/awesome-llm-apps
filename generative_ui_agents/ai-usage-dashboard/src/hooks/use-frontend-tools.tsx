"use client";

import { useFrontendTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import type { RefObject } from "react";

interface DataEditorToolCallbacks {
  setExpandedRow: (rowIndex: number | null) => void;
  scrollRef: RefObject<HTMLElement | null>;
  highlightRow: (rowIndex: number) => void;
  getQueryResult: () => {
    columns: string[];
    rows: Record<string, unknown>[];
  } | null;
}

export function useDataEditorTools(callbacks: DataEditorToolCallbacks) {
  useFrontendTool(
    {
      name: "highlightRow",
      description:
        "Scroll to a specific row in the data table and highlight it visually",
      parameters: z.object({
        rowIndex: z
          .number()
          .describe("Zero-based index of the row to highlight"),
      }),
      handler: async ({ rowIndex }) => {
        callbacks.highlightRow(rowIndex);
        return `Highlighted row ${rowIndex}`;
      },
    },
    [callbacks.highlightRow],
  );

  useFrontendTool(
    {
      name: "expandRow",
      description:
        "Expand the detail panel for a specific row in the data table",
      parameters: z.object({
        rowIndex: z.number().describe("Zero-based index of the row to expand"),
      }),
      handler: async ({ rowIndex }) => {
        callbacks.setExpandedRow(rowIndex);
        return `Expanded row ${rowIndex}`;
      },
    },
    [callbacks.setExpandedRow],
  );

  useFrontendTool(
    {
      name: "scrollToTop",
      description: "Scroll the data table back to the top",
      handler: async () => {
        callbacks.scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
        return "Scrolled to top";
      },
    },
    [callbacks.scrollRef],
  );

  useFrontendTool(
    {
      name: "exportAsCSV",
      description: "Export the current data table view as a CSV file download",
      handler: async () => {
        const result = callbacks.getQueryResult();
        if (!result || !result.rows.length) return "No data to export";

        const header = result.columns.join(",");
        const rows = result.rows.map((row) =>
          result.columns
            .map((col) => {
              const val = row[col];
              if (val === null) return "";
              const str = String(val);
              return str.includes(",") || str.includes('"')
                ? `"${str.replace(/"/g, '""')}"`
                : str;
            })
            .join(","),
        );
        const csv = [header, ...rows].join("\n");
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "data-export.csv";
        a.click();
        URL.revokeObjectURL(url);
        return `Exported ${result.rows.length} rows as CSV`;
      },
    },
    [callbacks.getQueryResult],
  );
}
