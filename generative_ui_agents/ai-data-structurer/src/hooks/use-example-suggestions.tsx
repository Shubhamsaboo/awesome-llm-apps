import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export const useExampleSuggestions = () => {
  useConfigureSuggestions({
    suggestions: [
      {
        title: "Structure CSV Data",
        message:
          "Here's some sales data:\n\nName,Region,Q1 Sales,Q2 Sales\nAcme Corp,West,45000,52000\nBeta Inc,East,38000,41000\nGamma Ltd,West,62000,58000\nDelta Co,East,29000,35000",
      },
      {
        title: "Structure JSON Data",
        message:
          'Structure this data:\n\n[{"name": "Acme", "region": "West", "revenue": 45000, "employees": 120}, {"name": "Beta", "region": "East", "revenue": 38000, "employees": 85}]',
      },
      {
        title: "Parse a Markdown Table",
        message:
          "Can you structure this?\n\n| Product | Category | Price | Stock |\n|---------|----------|-------|-------|\n| Widget A | Hardware | $29.99 | 150 |\n| Widget B | Software | $9.99 | unlimited |\n| Widget C | Hardware | $49.99 | 42 |",
      },
      {
        title: "Dashboard from Data (A2UI Dynamic)",
        message:
          "Show me a dashboard for this data:\n\nName,Region,Q1 Sales,Q2 Sales\nAcme Corp,West,45000,52000\nBeta Inc,East,38000,41000\nGamma Ltd,West,62000,58000\nDelta Co,East,29000,35000\n\nInclude total revenue, average per region, and a bar chart of Q1 vs Q2.",
      },
    ],
    available: "always",
  });
};
