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
      : [
          {
            title: "Try example documents",
            message:
              "Load the example documents and build a knowledge graph from them.",
          },
          {
            title: "Try example code",
            message:
              "Load the example code files and build a knowledge graph from them.",
          },
          {
            title: "Upload your files",
            message: "I'd like to upload my own files. How do I get started?",
          },
        ],
    available: "always",
  });
}
