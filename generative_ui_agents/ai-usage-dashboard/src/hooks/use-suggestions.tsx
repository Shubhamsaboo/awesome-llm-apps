"use client";

import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export function useSuggestions(hasResults: boolean) {
  useConfigureSuggestions({
    instructions: hasResults
      ? "Suggest exactly 3 follow-up actions a SaaS customer would take after viewing their data. Think like a customer: understand costs, check limits, take action. One should help them understand their bill. One should help them manage their usage. One should be an action (upgrade, set alert, export). Keep titles under 5 words."
      : "Suggest exactly 3 things a SaaS customer would want to see first when logging into their usage dashboard. Think: usage overview, cost breakdown, plan limits. Keep titles under 5 words.",
    minSuggestions: 3,
    maxSuggestions: 3,
  });
}
