/**
 * CopilotKit brand chart palette — Plus Jakarta Sans / brand color system.
 */
export const CHART_COLORS = [
  "#BEC2FF", // lilac-400
  "#85ECCE", // mint-400
  "#FFAC4D", // orange-400
  "#FFF388", // yellow-400
  "#189370", // mint-800
  "#EEE6FE", // primary-100
  "#FA5F67", // red-400
] as const;

export const CHART_CONFIG = {
  tooltipStyle: {
    backgroundColor: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    padding: "10px 14px",
    color: "var(--foreground)",
    fontSize: "13px",
    fontFamily: "var(--font-body)",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  },
};
