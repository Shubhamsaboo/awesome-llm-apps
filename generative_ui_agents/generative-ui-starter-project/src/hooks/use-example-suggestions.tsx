/**
 * Suggestion pills shown in the chat UI. Each suggestion triggers a specific
 * demo feature when clicked.
 *
 * Ordered from most constrained (fixed UI) to most open (freeform UI).
 *
 * Showcase mode (showcase.json) controls which pills are visually highlighted.
 * Highlight styling: globals.css (.a2ui-highlight, .opengenui-highlight)
 * A2UI agent tools: agent/src/a2ui_fixed_schema.py, a2ui_dynamic_schema.py
 * A2UI catalog: src/app/declarative-generative-ui/
 */
import { useConfigureSuggestions } from "@copilotkit/react-core/v2";
import showcaseConfig from "../../showcase.json";

const showcase = showcaseConfig.showcase;

export const useExampleSuggestions = () => {
  useConfigureSuggestions({
    suggestions: [
      {
        title: "Pie Chart (Controlled Generative UI)",
        message:
          "Show me a pie chart of our revenue distribution by category. Use the query_data tool to fetch the data first, then render it with the pieChart component.",
      },
      {
        title: "Bar Chart (Controlled Generative UI)",
        message:
          "Show me a bar chart of our expenses by category. Use the query_data tool to fetch the data first, then render it with the barChart component.",
      },
      {
        title: "Schedule Meeting (Human In The Loop)",
        message:
          "I'd like to schedule a 30-minute meeting to learn about CopilotKit. Please use the scheduleTime tool to let me pick a time.",
      },
      {
        title: "Search Flights (A2UI Fixed Schema)",
        message: "Find flights from SFO to JFK for next Tuesday.",
        className: showcase === "a2ui" ? "a2ui-highlight" : undefined,
      },
      {
        title: "Sales Dashboard (A2UI Dynamic)",
        message:
          "First use the query_data tool to fetch the financial sales data, then using A2UI, show me a sales dashboard with total revenue, new customers, and conversion rate metrics. Include a pie chart of revenue by category and a bar chart of monthly sales.",
        className: showcase === "a2ui" ? "a2ui-highlight" : undefined,
      },
      {
        title: "Excalidraw Diagram (MCP App)",
        message:
          "Use Excalidraw to create a simple network diagram showing a router connected to two switches, each connected to two computers.",
      },
      {
        title: "Calculator App (Open Generative UI)",
        message:
          "Using the generateSandboxedUi tool, build a modern calculator with standard buttons plus labeled metric shortcut buttons that insert their values into the display when clicked. Use sample company data.",
        className: showcase === "opengenui" ? "opengenui-highlight" : undefined,
      },
      {
        title: "Toggle Theme (Frontend Tools)",
        message: "Toggle the app theme using the toggleTheme tool.",
      },
      {
        title: "Task Manager (Shared State)",
        message:
          "Enable app mode and add three todos about learning CopilotKit: one about reading the docs, one about building a prototype, and one about exploring agent state.",
      },
    ],
    available: "always",
  });
};
