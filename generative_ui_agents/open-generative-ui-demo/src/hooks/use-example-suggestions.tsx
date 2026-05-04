/**
 * Suggestion pills shown in the chat UI. Every prompt here is designed to
 * trigger the runtime's `generateSandboxedUi` tool — the agent generates
 * complete HTML / CSS / JS that streams live into a sandboxed iframe inside
 * the chat. A handful query the local CSV first via the `query_data` tool to
 * show how data → generated visualization flows together.
 */
import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export const useExampleSuggestions = () => {
  useConfigureSuggestions({
    suggestions: [
      {
        title: "Calculator",
        message:
          "Using generateSandboxedUi, build a modern calculator with the standard buttons and a clean layout. Buttons should be clickable and update the display.",
      },
      {
        title: "Pomodoro Timer",
        message:
          "Using generateSandboxedUi, build a pomodoro timer with start, pause, and reset buttons and a circular progress ring. Default to a 25-minute work / 5-minute break cycle.",
      },
      {
        title: "Weather Card",
        message:
          "Using generateSandboxedUi, build a weather card for San Francisco showing current temp, conditions, a 5-day forecast row with icons, and a subtle gradient background. Use mock data.",
      },
      {
        title: "Revenue Dashboard",
        message:
          "First call query_data to fetch the company financials, then using generateSandboxedUi, render a KPI dashboard: total revenue, active customers, conversion rate as cards across the top, and a Chart.js bar chart of monthly revenue below. Load Chart.js from a CDN.",
      },
      {
        title: "Solar System",
        message:
          "Using generateSandboxedUi, build an animated solar system: sun in the center, eight planets orbiting at different speeds, with a CSS-only animation. Make it visually striking on a black background.",
      },
      {
        title: "Binary Search Visualizer",
        message:
          "Using generateSandboxedUi, build a step-through visualizer for binary search on a sorted array of 16 numbers. Show the low / mid / high pointers and a Next button that advances each step.",
      },
      {
        title: "Markdown Editor",
        message:
          "Using generateSandboxedUi, build a split-pane markdown editor: left side textarea, right side live preview. Load `marked` from a CDN. Pre-fill with a short example.",
      },
      {
        title: "Audio Equalizer",
        message:
          "Using generateSandboxedUi, build an animated audio equalizer — 20 vertical bars that bounce at different frequencies. Pure CSS animation, no audio input needed. Neon-on-black palette.",
      },
    ],
    available: "always",
  });
};
