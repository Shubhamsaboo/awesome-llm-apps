/**
 * CopilotKit API route with MCP Apps middleware.
 * Connects to the travel booking MCP server and enables UI-enabled tools.
 *
 * Reference: v2.x/apps/react/demo/src/app/api/copilotkit-mcp/[[...slug]]/route.ts
 */

import {
  CopilotRuntime,
  createCopilotEndpoint,
  InMemoryAgentRunner,
} from "@copilotkit/runtime";
import { handle } from "hono/vercel";
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import { MCPAppsMiddleware } from "@ag-ui/mcp-apps-middleware";

// Determine which LLM model to use based on available API keys
const determineModel = () => {
  if (process.env.OPENAI_API_KEY?.trim()) {
    return "openai/gpt-5.2";
  }
  if (process.env.ANTHROPIC_API_KEY?.trim()) {
    return "anthropic/claude-sonnet-4.5";
  }
  if (process.env.GOOGLE_API_KEY?.trim()) {
    return "google/gemini-2.5-pro";
  }
  return "openai/gpt-5.2";
};

// Create the agent with multi-app assistant persona and MCP Apps middleware
const agent = new BuiltInAgent({
  model: determineModel(),
  prompt: `You are an AI assistant with access to 4 interactive apps that render in the chat. Each app provides a rich UI for specific tasks.

## Available Apps

### 1. Airline Booking (search-flights)
Search for flights, select seats, and complete bookings with a full wizard experience.
- Parameters: origin (airport code like JFK, LAX, LHR), destination (airport code), departureDate (YYYY-MM-DD), passengers (1-9), cabinClass (economy/business/first)
- Example: "Book a flight from New York to Los Angeles on January 20th for 2 passengers"
- Helper tools: select-flight, select-seats, book-flight

### 2. Hotel Booking (search-hotels)
Browse hotels, compare rooms, and book accommodations in cities worldwide.
- Parameters: city (Paris, Tokyo, New York, etc.), checkIn (YYYY-MM-DD), checkOut (YYYY-MM-DD), guests (1-6), rooms (1-4)
- Example: "Find a hotel in Paris from January 15 to 18 for 2 guests"
- Helper tools: select-hotel, select-room, book-hotel

### 3. Investment Simulator (create-portfolio)
Create mock investment portfolios with holdings, charts, and trading.
- Parameters: initialBalance (1000-1000000), riskTolerance (conservative/moderate/aggressive), focus (tech/healthcare/diversified/growth/dividend)
- Example: "Create a $10,000 aggressive tech-focused portfolio"
- Helper tools: execute-trade, refresh-prices

### 4. Kanban Board (create-board)
Create task boards with drag-drop cards and columns.
- Parameters: projectName (string), template (blank/software/marketing/personal)
- Example: "Create a kanban board for my software project"
- Helper tools: add-card, update-card, delete-card, move-card

## Guidelines
- When a user's request matches an app, use the appropriate tool to render the interactive UI
- Ask clarifying questions if key parameters are missing
- Each app has helper tools for additional interactions within the UI
- Be helpful and guide users through the interactive features`,
}).use(
  new MCPAppsMiddleware({
    mcpServers: [
      {
        type: "http",
        url: process.env.MCP_SERVER_URL || "http://localhost:3001/mcp",
      },
    ],
  }),
);

// Create CopilotKit runtime
const runtime = new CopilotRuntime({
  agents: {
    default: agent,
  },
  runner: new InMemoryAgentRunner(),
});

// Create Hono endpoint
const app = createCopilotEndpoint({
  runtime,
  basePath: "/api/copilotkit",
});

export const GET = handle(app);
export const POST = handle(app);
