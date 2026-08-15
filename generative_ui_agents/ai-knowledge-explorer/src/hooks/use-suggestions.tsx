"use client";

import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export function useSuggestions(hasGraph: boolean) {
  useConfigureSuggestions({
    suggestions: hasGraph
      ? [
          {
            title: "Find deeper connections",
            message:
              "Find deeper connections between the nodes in the knowledge graph.",
          },
          {
            title: "Summarize what you found",
            message:
              "Summarize the key themes and relationships in the knowledge graph.",
          },
          {
            title: "Trace dependencies",
            message:
              "Trace the dependency chain — which modules depend on which, and where are the coupling hotspots?",
          },
        ]
      : [],
    available: "always",
  });
}
