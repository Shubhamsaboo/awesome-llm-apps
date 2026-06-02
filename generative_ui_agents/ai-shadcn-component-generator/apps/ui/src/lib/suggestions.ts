import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export function useInitialSuggestions() {
  useConfigureSuggestions({
    suggestions: [
      {
        title: "Make a dashboard",
        message: "Generate a simple dashboard with a title, menu and 2 chart columns.",
      },
      {
        title: "Research report",
        message:
          "Research the best pizza in San Francisco and make a report about it with the data you find.",
      },
      {
        title: "Mixed-media",
        message:
          "Get creative and use your components to give me a mixed-media fairy-tale of your choosing.",
      },
    ],
    available: "before-first-message",
  });
}
