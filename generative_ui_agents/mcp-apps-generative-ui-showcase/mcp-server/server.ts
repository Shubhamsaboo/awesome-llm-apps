/**
 * MCP Server for Travel Booking Demo.
 * Registers airline and hotel booking tools with travel app UI resources.
 *
 * Pattern from: v2.x/apps/react/demo/mcp-apps/server.ts
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import express, { Request, Response } from "express";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolResult,
  isInitializeRequest,
  ReadResourceResult,
  Resource,
} from "@modelcontextprotocol/sdk/types.js";
import { InMemoryEventStore } from "@modelcontextprotocol/sdk/examples/shared/inMemoryEventStore.js";
import cors from "cors";
import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";

// Import flights logic
import {
  searchFlights,
  selectFlight,
  selectSeats,
  createBooking,
} from "./src/flights.js";

// Import hotels logic
import {
  searchHotels,
  selectHotel,
  selectRoom,
  createHotelBooking,
} from "./src/hotels.js";

// Import trading logic
import {
  createPortfolio,
  executeTrade,
  refreshPrices,
  getStocks,
  Portfolio,
} from "./src/stocks.js";

// Import kanban logic
import {
  createBoard,
  addCard,
  updateCard,
  deleteCard,
  moveCard,
  Board,
} from "./src/kanban.js";

// MCP Apps Extension protocol constant
const RESOURCE_URI_META_KEY = "ui/resourceUri";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Store active portfolios by session
const activePortfolios: Map<string, Portfolio> = new Map();

// Store active boards by session
const activeBoards: Map<string, Board> = new Map();

// Load UI HTML file from apps/dist/
// __dirname points to dist/ after TypeScript compilation, but to mcp-server/ during dev (tsx)
const loadHtml = async (name: string): Promise<string> => {
  // Check if we're running from dist/ (production) or source (development)
  const isProduction = __dirname.endsWith("dist");
  const basePath = isProduction ? path.join(__dirname, "..") : __dirname;
  const htmlPath = path.join(basePath, "apps", "dist", `${name}.html`);
  try {
    return await fs.readFile(htmlPath, "utf-8");
  } catch {
    // Return placeholder HTML if not yet built
    return `<!DOCTYPE html>
<html>
<head><title>${name}</title></head>
<body>
  <div style="padding: 20px; font-family: system-ui;">
    <h2>${name} Loading...</h2>
    <p>The app UI needs to be built. Run:</p>
    <code>npm run build:app</code>
  </div>
</body>
</html>`;
  }
};

// Create the MCP server instance
const getServer = async () => {
  const server = new McpServer(
    {
      name: "travel-booking-mcp-server",
      version: "1.0.0",
    },
    { capabilities: { logging: {} } },
  );

  // Load app HTML files
  const flightsAppHtml = await loadHtml("flights-app");
  const hotelsAppHtml = await loadHtml("hotels-app");
  const tradingAppHtml = await loadHtml("trading-app");
  const kanbanAppHtml = await loadHtml("kanban-app");

  // Helper to register a resource
  const registerResource = (resource: Resource, htmlContent: string) => {
    server.registerResource(
      resource.name,
      resource.uri,
      resource,
      async (): Promise<ReadResourceResult> => ({
        contents: [
          {
            uri: resource.uri,
            mimeType: resource.mimeType,
            text: htmlContent,
          },
        ],
      }),
    );
    return resource;
  };

  // Register the flights app UI resource
  const flightsResource = registerResource(
    {
      name: "flights-app-template",
      uri: "ui://flights/flights-app.html",
      title: "Airline Booking",
      description:
        "Interactive flight search and booking wizard with seat selection",
      mimeType: "text/html+mcp",
    },
    flightsAppHtml,
  );

  // Register the hotels app UI resource
  const hotelsResource = registerResource(
    {
      name: "hotels-app-template",
      uri: "ui://hotels/hotels-app.html",
      title: "Hotel Booking",
      description:
        "Interactive hotel search and booking wizard with room selection",
      mimeType: "text/html+mcp",
    },
    hotelsAppHtml,
  );

  // Register the trading app UI resource
  const tradingResource = registerResource(
    {
      name: "trading-app-template",
      uri: "ui://trading/trading-app.html",
      title: "Investment Simulator",
      description:
        "Interactive portfolio UI with holdings, charts, and trading",
      mimeType: "text/html+mcp",
    },
    tradingAppHtml,
  );

  // Register the kanban app UI resource
  const kanbanResource = registerResource(
    {
      name: "kanban-app-template",
      uri: "ui://kanban/kanban-app.html",
      title: "Kanban Board",
      description: "Interactive task board with drag-drop cards and columns",
      mimeType: "text/html+mcp",
    },
    kanbanAppHtml,
  );

  // ============================================
  // AIRLINE BOOKING TOOLS
  // ============================================

  // Register search-flights tool (main tool with UI)
  server.registerTool(
    "search-flights",
    {
      title: "Search Flights",
      description:
        "Searches for available flights between two airports. Returns an interactive booking wizard UI.",
      inputSchema: {
        origin: z
          .string()
          .describe("Origin airport code (e.g., JFK, LAX, LHR)"),
        destination: z.string().describe("Destination airport code"),
        departureDate: z
          .string()
          .describe("Departure date in YYYY-MM-DD format"),
        passengers: z
          .number()
          .min(1)
          .max(9)
          .describe("Number of passengers (1-9)"),
        cabinClass: z
          .enum(["economy", "business", "first"])
          .optional()
          .describe("Cabin class (default: economy)"),
      },
      _meta: {
        [RESOURCE_URI_META_KEY]: flightsResource.uri,
      },
    },
    async ({
      origin,
      destination,
      departureDate,
      passengers,
      cabinClass,
    }): Promise<CallToolResult> => {
      try {
        const search = searchFlights({
          origin,
          destination,
          departureDate,
          passengers,
          cabinClass: cabinClass || "economy",
        });

        const flightSummary = search.flights
          .slice(0, 3)
          .map(
            (f) =>
              `${f.airline.code}${f.flightNumber.slice(2)} ${f.departureTime}-${f.arrivalTime} $${f.price}`,
          )
          .join(", ");

        return {
          content: [
            {
              type: "text",
              text: `Found ${search.flights.length} flights from ${origin} to ${destination} on ${departureDate}:\n\n${flightSummary}...`,
            },
          ],
          structuredContent: {
            search,
            summary: {
              flightCount: search.flights.length,
              origin,
              destination,
              date: departureDate,
              passengers,
            },
          },
        };
      } catch (error) {
        return {
          content: [
            { type: "text", text: `Error: ${(error as Error).message}` },
          ],
          structuredContent: {
            success: false,
            error: (error as Error).message,
          },
        };
      }
    },
  );

  // Register select-flight tool (helper for UI)
  server.registerTool(
    "select-flight",
    {
      title: "Select Flight",
      description:
        "Selects a flight from search results and returns the seat map",
      inputSchema: {
        searchId: z.string().describe("The search session ID"),
        flightId: z.string().describe("The flight ID to select"),
      },
    },
    async ({ searchId, flightId }): Promise<CallToolResult> => {
      const result = selectFlight(searchId, flightId);

      if (!result) {
        return {
          content: [{ type: "text", text: "Flight or search not found." }],
          structuredContent: {
            success: false,
            error: "Flight or search not found",
          },
        };
      }

      return {
        content: [
          {
            type: "text",
            text: `Selected ${result.flight.airline.name} ${result.flight.flightNumber} (${result.flight.departureTime}-${result.flight.arrivalTime}). Please choose your seats.`,
          },
        ],
        structuredContent: {
          success: true,
          flight: result.flight,
          seatMap: result.seatMap,
        },
      };
    },
  );

  // Register select-seats tool (helper for UI)
  server.registerTool(
    "select-seats",
    {
      title: "Select Seats",
      description: "Selects seats for the chosen flight",
      inputSchema: {
        searchId: z.string().describe("The search session ID"),
        flightId: z.string().describe("The flight ID"),
        seats: z
          .array(z.string())
          .describe("Array of seat IDs (e.g., ['12A', '12B'])"),
      },
    },
    async ({ searchId, flightId, seats }): Promise<CallToolResult> => {
      const result = selectSeats(searchId, flightId, seats);

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: result.success,
          selectedSeats: result.selectedSeats,
          totalSeatFee: result.totalSeatFee,
          error: result.success ? undefined : result.message,
        },
      };
    },
  );

  // Register book-flight tool (helper for UI)
  server.registerTool(
    "book-flight",
    {
      title: "Book Flight",
      description: "Completes the flight booking with passenger details",
      inputSchema: {
        searchId: z.string().describe("The search session ID"),
        passengers: z
          .array(
            z.object({
              name: z.string().describe("Passenger full name"),
              email: z.string().describe("Passenger email"),
              phone: z.string().describe("Passenger phone number"),
            }),
          )
          .describe("Passenger information"),
      },
    },
    async ({ searchId, passengers }): Promise<CallToolResult> => {
      const result = createBooking(searchId, passengers);

      if (!result.success || !result.booking) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      return {
        content: [
          {
            type: "text",
            text: `Booking confirmed! Confirmation: ${result.booking.confirmationNumber}\n\nFlight: ${result.booking.flight.airline.name} ${result.booking.flight.flightNumber}\nRoute: ${result.booking.flight.origin.code} → ${result.booking.flight.destination.code}\nSeats: ${result.booking.seats.join(", ")}\nTotal: $${result.booking.totalPrice.toFixed(2)}`,
          },
        ],
        structuredContent: {
          success: true,
          booking: result.booking,
        },
      };
    },
  );

  // ============================================
  // HOTEL BOOKING TOOLS
  // ============================================

  // Register search-hotels tool (main tool with UI)
  server.registerTool(
    "search-hotels",
    {
      title: "Search Hotels",
      description:
        "Searches for available hotels in a city. Returns an interactive booking wizard UI.",
      inputSchema: {
        city: z.string().describe("City name (e.g., Paris, New York, Tokyo)"),
        checkIn: z.string().describe("Check-in date in YYYY-MM-DD format"),
        checkOut: z.string().describe("Check-out date in YYYY-MM-DD format"),
        guests: z.number().min(1).max(6).describe("Number of guests (1-6)"),
        rooms: z
          .number()
          .min(1)
          .max(4)
          .optional()
          .describe("Number of rooms needed (default: 1)"),
      },
      _meta: {
        [RESOURCE_URI_META_KEY]: hotelsResource.uri,
      },
    },
    async ({
      city,
      checkIn,
      checkOut,
      guests,
      rooms,
    }): Promise<CallToolResult> => {
      try {
        const search = searchHotels({
          city,
          checkIn,
          checkOut,
          guests,
          rooms: rooms || 1,
        });

        const hotelSummary = search.hotels
          .slice(0, 3)
          .map(
            (h) =>
              `${"★".repeat(h.stars)} ${h.name} (${h.rating}/10) from $${h.pricePerNight}/night`,
          )
          .join("\n");

        return {
          content: [
            {
              type: "text",
              text: `Found ${search.hotels.length} hotels in ${city} for ${search.searchParams.nights} night(s):\n\n${hotelSummary}`,
            },
          ],
          structuredContent: {
            search,
            summary: {
              hotelCount: search.hotels.length,
              city,
              checkIn,
              checkOut,
              nights: search.searchParams.nights,
              guests,
            },
          },
        };
      } catch (error) {
        return {
          content: [
            { type: "text", text: `Error: ${(error as Error).message}` },
          ],
          structuredContent: {
            success: false,
            error: (error as Error).message,
          },
        };
      }
    },
  );

  // Register select-hotel tool (helper for UI)
  server.registerTool(
    "select-hotel",
    {
      title: "Select Hotel",
      description:
        "Selects a hotel from search results and returns available rooms",
      inputSchema: {
        searchId: z.string().describe("The search session ID"),
        hotelId: z.string().describe("The hotel ID to select"),
      },
    },
    async ({ searchId, hotelId }): Promise<CallToolResult> => {
      const result = selectHotel(searchId, hotelId);

      if (!result) {
        return {
          content: [{ type: "text", text: "Hotel or search not found." }],
          structuredContent: {
            success: false,
            error: "Hotel or search not found",
          },
        };
      }

      const roomSummary = result.rooms
        .map((r) => `${r.name}: $${r.pricePerNight}/night`)
        .join(", ");

      return {
        content: [
          {
            type: "text",
            text: `Selected ${result.hotel.name} (${"★".repeat(result.hotel.stars)}). Available rooms: ${roomSummary}`,
          },
        ],
        structuredContent: {
          success: true,
          hotel: result.hotel,
          rooms: result.rooms,
        },
      };
    },
  );

  // Register select-room tool (helper for UI)
  server.registerTool(
    "select-room",
    {
      title: "Select Room",
      description: "Selects a room type and quantity for the booking",
      inputSchema: {
        searchId: z.string().describe("The search session ID"),
        hotelId: z.string().describe("The hotel ID"),
        roomId: z.string().describe("The room type ID"),
        quantity: z.number().min(1).max(4).describe("Number of rooms"),
      },
    },
    async ({
      searchId,
      hotelId,
      roomId,
      quantity,
    }): Promise<CallToolResult> => {
      const result = selectRoom(searchId, hotelId, roomId, quantity);

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: result.success,
          room: result.room,
          totalPrice: result.totalPrice,
          error: result.success ? undefined : result.message,
        },
      };
    },
  );

  // Register book-hotel tool (helper for UI)
  server.registerTool(
    "book-hotel",
    {
      title: "Book Hotel",
      description: "Completes the hotel booking with guest details",
      inputSchema: {
        searchId: z.string().describe("The search session ID"),
        guests: z
          .array(
            z.object({
              name: z.string().describe("Guest full name"),
              email: z.string().describe("Guest email"),
            }),
          )
          .describe("Guest information"),
        specialRequests: z
          .string()
          .optional()
          .describe("Special requests for the hotel"),
      },
    },
    async ({ searchId, guests, specialRequests }): Promise<CallToolResult> => {
      const result = createHotelBooking(searchId, guests, specialRequests);

      if (!result.success || !result.booking) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      return {
        content: [
          {
            type: "text",
            text: `Booking confirmed! Confirmation: ${result.booking.confirmationNumber}\n\nHotel: ${result.booking.hotel.name}\nRoom: ${result.booking.roomQuantity}x ${result.booking.room.name}\nDates: ${result.booking.checkIn} to ${result.booking.checkOut} (${result.booking.nights} nights)\nTotal: $${result.booking.totalPrice.toFixed(2)}`,
          },
        ],
        structuredContent: {
          success: true,
          booking: result.booking,
        },
      };
    },
  );

  // ============================================
  // INVESTMENT SIMULATOR TOOLS
  // ============================================

  // Register create-portfolio tool (main tool with UI)
  server.registerTool(
    "create-portfolio",
    {
      title: "Create Portfolio",
      description:
        "Creates an investment portfolio based on initial balance, risk tolerance, and focus area. Returns an interactive UI for trading.",
      inputSchema: {
        initialBalance: z
          .number()
          .min(1000)
          .max(1000000)
          .describe("Starting cash balance (1000-1000000)"),
        riskTolerance: z
          .enum(["conservative", "moderate", "aggressive"])
          .describe("Risk tolerance level"),
        focus: z
          .enum(["tech", "healthcare", "diversified", "growth", "dividend"])
          .describe("Portfolio focus area"),
      },
      _meta: {
        [RESOURCE_URI_META_KEY]: tradingResource.uri,
      },
    },
    async ({
      initialBalance,
      riskTolerance,
      focus,
    }): Promise<CallToolResult> => {
      // Create the portfolio
      const { portfolio, availableStocks } = createPortfolio({
        initialBalance,
        riskTolerance,
        focus,
      });

      // Store portfolio for later trades
      activePortfolios.set(portfolio.id, portfolio);

      // Build holdings summary
      const holdingsSummary = portfolio.holdings
        .slice(0, 3)
        .map((h) => `${h.symbol}: ${h.shares} shares`)
        .join(", ");

      const plSign = portfolio.totalProfitLoss >= 0 ? "+" : "";

      return {
        content: [
          {
            type: "text",
            text: `Created ${focus} portfolio ($${initialBalance.toLocaleString()}, ${riskTolerance} risk):\n\nTotal Value: $${portfolio.totalValue.toLocaleString()}\nP/L: ${plSign}$${portfolio.totalProfitLoss.toFixed(2)}\nCash: $${portfolio.cash.toLocaleString()}\n\nHoldings: ${holdingsSummary}...`,
          },
        ],
        structuredContent: {
          portfolio,
          availableStocks,
          summary: {
            totalValue: portfolio.totalValue,
            profitLoss: portfolio.totalProfitLoss,
            cash: portfolio.cash,
            holdingsCount: portfolio.holdings.length,
            allocation: portfolio.allocation,
          },
        },
      };
    },
  );

  // Register execute-trade tool (helper for UI callbacks)
  server.registerTool(
    "execute-trade",
    {
      title: "Execute Trade",
      description: "Buys or sells shares of a stock in the portfolio",
      inputSchema: {
        portfolioId: z.string().describe("The portfolio ID"),
        symbol: z.string().describe("Stock symbol to trade"),
        action: z.enum(["buy", "sell"]).describe("Trade action"),
        quantity: z.number().min(1).describe("Number of shares"),
      },
    },
    async ({
      portfolioId,
      symbol,
      action,
      quantity,
    }): Promise<CallToolResult> => {
      const result = executeTrade(portfolioId, symbol, action, quantity);

      if (!result.success) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      // Update stored portfolio
      if (result.portfolio) {
        activePortfolios.set(portfolioId, result.portfolio);
      }

      // Get available stocks for the UI
      const allStocks = getStocks();
      const holdingSymbols = new Set(
        result.portfolio?.holdings.map((h) => h.symbol) || [],
      );
      const availableStocks = allStocks.filter(
        (s) => !holdingSymbols.has(s.symbol),
      );

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: true,
          trade: result.trade,
          portfolio: result.portfolio,
          availableStocks,
        },
      };
    },
  );

  // Register refresh-prices tool (helper for UI)
  server.registerTool(
    "refresh-prices",
    {
      title: "Refresh Prices",
      description: "Simulates market movement by updating stock prices",
      inputSchema: {
        portfolioId: z.string().describe("The portfolio ID"),
      },
    },
    async ({ portfolioId }): Promise<CallToolResult> => {
      const result = refreshPrices(portfolioId);

      if (!result) {
        return {
          content: [
            { type: "text", text: `Portfolio ${portfolioId} not found.` },
          ],
          structuredContent: { success: false, error: "Portfolio not found" },
        };
      }

      // Update stored portfolio
      activePortfolios.set(portfolioId, result.portfolio);

      const plSign = result.portfolio.totalProfitLoss >= 0 ? "+" : "";

      return {
        content: [
          {
            type: "text",
            text: `Prices refreshed. Portfolio: $${result.portfolio.totalValue.toLocaleString()} (${plSign}$${result.portfolio.totalProfitLoss.toFixed(2)})`,
          },
        ],
        structuredContent: {
          success: true,
          portfolio: result.portfolio,
          availableStocks: result.availableStocks,
        },
      };
    },
  );

  // ============================================
  // KANBAN BOARD TOOLS
  // ============================================

  // Register create-board tool (main tool with UI)
  server.registerTool(
    "create-board",
    {
      title: "Create Kanban Board",
      description:
        "Creates a kanban board for project management with customizable columns and cards. Returns an interactive drag-drop UI.",
      inputSchema: {
        projectName: z.string().describe("Name for the project board"),
        template: z
          .enum(["blank", "software", "marketing", "personal"])
          .describe(
            "Board template with pre-configured columns and sample cards",
          ),
      },
      _meta: {
        [RESOURCE_URI_META_KEY]: kanbanResource.uri,
      },
    },
    async ({ projectName, template }): Promise<CallToolResult> => {
      // Create the board
      const board = createBoard(projectName, template);

      // Store board for later operations
      activeBoards.set(board.id, board);

      const totalCards = board.columns.reduce(
        (sum, c) => sum + c.cards.length,
        0,
      );

      return {
        content: [
          {
            type: "text",
            text: `Created "${projectName}" board (${template} template):\n\nColumns: ${board.columns.map((c) => c.name).join(", ")}\nTotal cards: ${totalCards}`,
          },
        ],
        structuredContent: {
          board,
          summary: {
            name: board.name,
            columnsCount: board.columns.length,
            cardsCount: totalCards,
            template,
          },
        },
      };
    },
  );

  // Register move-card tool (helper for drag-drop)
  server.registerTool(
    "move-card",
    {
      title: "Move Card",
      description: "Moves a card to a different column on the board",
      inputSchema: {
        boardId: z.string().describe("The board ID"),
        cardId: z.string().describe("The card ID to move"),
        targetColumnId: z.string().describe("Target column ID"),
        position: z
          .number()
          .optional()
          .describe("Position in column (default: end)"),
      },
    },
    async ({
      boardId,
      cardId,
      targetColumnId,
      position,
    }): Promise<CallToolResult> => {
      const result = moveCard(boardId, cardId, targetColumnId, position);

      if (!result.success) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      // Update stored board
      if (result.board) {
        activeBoards.set(boardId, result.board);
      }

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: true,
          board: result.board,
          card: result.card,
        },
      };
    },
  );

  // Register add-card tool (helper for UI)
  server.registerTool(
    "add-card",
    {
      title: "Add Card",
      description: "Adds a new card to a column",
      inputSchema: {
        boardId: z.string().describe("The board ID"),
        columnId: z.string().describe("The column ID"),
        title: z.string().describe("Card title"),
        description: z.string().optional().describe("Card description"),
        priority: z
          .enum(["low", "medium", "high"])
          .optional()
          .describe("Card priority"),
      },
    },
    async ({
      boardId,
      columnId,
      title,
      description,
      priority,
    }): Promise<CallToolResult> => {
      const result = addCard(boardId, columnId, {
        title,
        description,
        priority: priority || "medium",
        tags: [],
      });

      if (!result.success) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      // Update stored board
      if (result.board) {
        activeBoards.set(boardId, result.board);
      }

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: true,
          board: result.board,
          card: result.card,
        },
      };
    },
  );

  // Register update-card tool (helper for UI)
  server.registerTool(
    "update-card",
    {
      title: "Update Card",
      description: "Updates an existing card's title, description, or priority",
      inputSchema: {
        boardId: z.string().describe("The board ID"),
        cardId: z.string().describe("The card ID"),
        updates: z
          .object({
            title: z.string().optional(),
            description: z.string().optional(),
            priority: z.enum(["low", "medium", "high"]).optional(),
          })
          .describe("Fields to update"),
      },
    },
    async ({ boardId, cardId, updates }): Promise<CallToolResult> => {
      const result = updateCard(boardId, cardId, updates);

      if (!result.success) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      // Update stored board
      if (result.board) {
        activeBoards.set(boardId, result.board);
      }

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: true,
          board: result.board,
          card: result.card,
        },
      };
    },
  );

  // Register delete-card tool (helper for UI)
  server.registerTool(
    "delete-card",
    {
      title: "Delete Card",
      description: "Removes a card from the board",
      inputSchema: {
        boardId: z.string().describe("The board ID"),
        cardId: z.string().describe("The card ID to delete"),
      },
    },
    async ({ boardId, cardId }): Promise<CallToolResult> => {
      const result = deleteCard(boardId, cardId);

      if (!result.success) {
        return {
          content: [{ type: "text", text: result.message }],
          structuredContent: { success: false, error: result.message },
        };
      }

      // Update stored board
      if (result.board) {
        activeBoards.set(boardId, result.board);
      }

      return {
        content: [{ type: "text", text: result.message }],
        structuredContent: {
          success: true,
          board: result.board,
          deletedCard: result.card,
        },
      };
    },
  );

  return server;
};

// Express server setup
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3001;

const app = express();
app.use(express.json());
app.use(
  cors({
    origin: "*",
    exposedHeaders: ["Mcp-Session-Id"],
  }),
);

// Session management for MCP connections
const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};

// MCP POST handler - main entry point for MCP requests
const mcpPostHandler = async (req: Request, res: Response) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  try {
    let transport: StreamableHTTPServerTransport;

    if (sessionId && transports[sessionId]) {
      // Existing session
      transport = transports[sessionId];
    } else if (!sessionId && isInitializeRequest(req.body)) {
      // New session initialization - eventStore enables resumability for MCP Apps
      const eventStore = new InMemoryEventStore();
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        eventStore,
        onsessioninitialized: (sid) => {
          console.log(`[MCP] Session initialized: ${sid}`);
          transports[sid] = transport;
        },
      });

      transport.onclose = () => {
        const sid = transport.sessionId;
        if (sid && transports[sid]) {
          console.log(`[MCP] Session closed: ${sid}`);
          delete transports[sid];
        }
      };

      const server = await getServer();
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
      return;
    } else {
      // Invalid request
      res.status(400).json({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Bad Request: No valid session ID" },
        id: null,
      });
      return;
    }

    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("[MCP] Error handling request:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: "Internal server error" },
        id: null,
      });
    }
  }
};

// Routes
app.post("/mcp", mcpPostHandler);

app.get("/mcp", async (req: Request, res: Response) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send("Invalid or missing session ID");
    return;
  }
  const transport = transports[sessionId];
  await transport.handleRequest(req, res);
});

app.delete("/mcp", async (req: Request, res: Response) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send("Invalid or missing session ID");
    return;
  }
  try {
    const transport = transports[sessionId];
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error("[MCP] Error handling session termination:", error);
    if (!res.headersSent) {
      res.status(500).send("Error processing session termination");
    }
  }
});

// Health check endpoint
app.get("/health", (_req: Request, res: Response) => {
  res.json({
    status: "ok",
    server: "travel-booking-mcp",
    sessions: Object.keys(transports).length,
  });
});

// Start server
app.listen(PORT, () => {
  console.log(
    `[Travel Booking MCP Server] Running at http://localhost:${PORT}/mcp`,
  );
  console.log(`[Health Check] http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on("SIGINT", async () => {
  console.log("\n[MCP] Shutting down...");
  for (const sessionId in transports) {
    try {
      await transports[sessionId].close();
      delete transports[sessionId];
    } catch (error) {
      console.error(`[MCP] Error closing session ${sessionId}:`, error);
    }
  }
  process.exit(0);
});
