"use client";

import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export function useSuggestions(hasResults: boolean) {
  useConfigureSuggestions({
    instructions: hasResults
      ? "Suggest exactly 3 follow-up actions based on what the user is currently viewing. Be specific — reference actual column names, statuses, or patterns visible in the data. One suggestion should be an edit/update action. Keep titles under 5 words. Do NOT suggest more than 3."
      : "Suggest exactly 3 starting queries for exploring a SaaS accounts database with accounts, usage metrics, and invoices. Be specific and actionable. Keep titles under 5 words. Do NOT suggest more than 3.",
    minSuggestions: 3,
    maxSuggestions: 3,
  });
}
