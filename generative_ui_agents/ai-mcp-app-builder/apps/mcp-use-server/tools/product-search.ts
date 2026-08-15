import { MCPServer, object, text, widget } from "mcp-use/server";
import { z } from "zod";

// Fruit catalogue — shared between search-tools and get-fruit-details
const fruits = [
  { fruit: "mango", color: "bg-[#FBF1E1] dark:bg-[#FBF1E1]/10" },
  { fruit: "pineapple", color: "bg-[#f8f0d9] dark:bg-[#f8f0d9]/10" },
  { fruit: "cherries", color: "bg-[#E2EDDC] dark:bg-[#E2EDDC]/10" },
  { fruit: "coconut", color: "bg-[#fbedd3] dark:bg-[#fbedd3]/10" },
  { fruit: "apricot", color: "bg-[#fee6ca] dark:bg-[#fee6ca]/10" },
  { fruit: "blueberry", color: "bg-[#e0e6e6] dark:bg-[#e0e6e6]/10" },
  { fruit: "grapes", color: "bg-[#f4ebe2] dark:bg-[#f4ebe2]/10" },
  { fruit: "watermelon", color: "bg-[#e6eddb] dark:bg-[#e6eddb]/10" },
  { fruit: "orange", color: "bg-[#fdebdf] dark:bg-[#fdebdf]/10" },
  { fruit: "avocado", color: "bg-[#ecefda] dark:bg-[#ecefda]/10" },
  { fruit: "apple", color: "bg-[#F9E7E4] dark:bg-[#F9E7E4]/10" },
  { fruit: "pear", color: "bg-[#f1f1cf] dark:bg-[#f1f1cf]/10" },
  { fruit: "plum", color: "bg-[#ece5ec] dark:bg-[#ece5ec]/10" },
  { fruit: "banana", color: "bg-[#fdf0dd] dark:bg-[#fdf0dd]/10" },
  { fruit: "strawberry", color: "bg-[#f7e6df] dark:bg-[#f7e6df]/10" },
  { fruit: "lemon", color: "bg-[#feeecd] dark:bg-[#feeecd]/10" },
];

/**
 * Registers the product-search MCP App widget and its companion data tool.
 *
 * Widget UI:  resources/product-search-result/widget.tsx
 *             ↑ This is the React component rendered in the iframe.
 *
 * Tools registered here:
 *   - search-tools       → triggers the widget UI (visual search results carousel)
 *   - get-fruit-details  → data tool called from within the widget via useCallTool()
 */
export function register(server: MCPServer) {
  // MCP App widget tool — calls return widget({ props }) which renders the React component
  server.tool(
    {
      name: "search-tools",
      description:
        "Search for fruits and display the results in a visual widget",
      schema: z.object({
        query: z.string().optional().describe("Search query to filter fruits"),
      }),
      widget: {
        name: "product-search-result", // must match the folder name under resources/
        invoking: "Searching...",
        invoked: "Results loaded",
      },
      _meta: {
        // Preview data shown in MCP UI Studio when no live call has been made yet
        "ui/previewData": {
          query: "tropical",
          results: [
            { fruit: "mango", color: "bg-[#FBF1E1] dark:bg-[#FBF1E1]/10" },
            { fruit: "pineapple", color: "bg-[#f8f0d9] dark:bg-[#f8f0d9]/10" },
            { fruit: "coconut", color: "bg-[#fbedd3] dark:bg-[#fbedd3]/10" },
            { fruit: "banana", color: "bg-[#fdf0dd] dark:bg-[#fdf0dd]/10" },
          ],
        },
      },
    },
    async ({ query }) => {
      const results = fruits.filter(
        (f) => !query || f.fruit.toLowerCase().includes(query.toLowerCase()),
      );
      // Simulate network delay to demonstrate the loading state in the widget
      await new Promise((resolve) => setTimeout(resolve, 2000));
      return widget({
        props: { query: query ?? "", results },
        output: text(
          `Found ${results.length} fruits matching "${query ?? "all"}"`,
        ),
      });
    },
  );

  // Companion data tool — called from within the widget via useCallTool("get-fruit-details")
  server.tool(
    {
      name: "get-fruit-details",
      description: "Get detailed information about a specific fruit",
      schema: z.object({
        fruit: z.string().describe("The fruit name"),
      }),
      outputSchema: z.object({
        fruit: z.string(),
        color: z.string(),
        facts: z.array(z.string()),
      }),
    },
    async ({ fruit }) => {
      const found = fruits.find(
        (f) => f.fruit?.toLowerCase() === fruit?.toLowerCase(),
      );
      return object({
        fruit: found?.fruit ?? fruit,
        color: found?.color ?? "unknown",
        facts: [
          `${fruit} is a delicious fruit`,
          `Color: ${found?.color ?? "unknown"}`,
        ],
      });
    },
  );
}
