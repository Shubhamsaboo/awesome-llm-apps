# Architecture

Design UX flows and API shape for your ChatGPT app.

## Concepts

A **tool** is a backend action with no UI. It takes input and returns structured output. Use for CRUD operations, API calls, and actions (checkout, submit, cancel).

A **widget** is a tool with a UI. It renders the tool output visually. The UI is a React component that can:

- Navigate multiple views (search -> detail -> confirmation)
- Manage its own state (selections, filters, form inputs)
- Call other tools to fetch data or trigger actions

## Step 1: Identify UX Flows

A **flow** is an end-to-end user journey that accomplishes one goal.

Extract flows from your spec's core actions. **Stick to the spec** -- don't invent flows.

**Example:**

Spec: "Book flights by destination and dates, and cancel existing bookings."

Flows:

```
Book flight:     Search -> Select -> Checkout
Cancel booking:  Provide info -> Confirm cancellation
```

## Step 2: Does the Flow Need UI?

**YES → widget** if:

- Browsing/comparing multiple items (search results, listings)
- Visual data improves understanding (maps, charts, images, color swatches)
- Selections are easier in a visual layout (seat picker, calendar)

**NO → tool only** if:

- Inputs are naturally conversational (amounts, dates, descriptions)
- Output is simple text (confirmation ID, status message)
- No visual element would meaningfully improve the experience

## Step 3: Design the API

### Naming

Both widgets and tools start with a verb: `search-flights`, `get-details`, `create-checkout`.

### One widget per flow

Different flows can have separate widgets. Don't split one flow into multiple widgets.

❌ `search-flights` widget + `view-flight` widget (same flow -> merge into one widget)
✅ `search-flights` widget + `manage-bookings` widget (different flows)

### Don't duplicate

Widget output is returned to the LLM for conversation. Don't create a tool that fetches the same data.

❌ `search-flights` widget + `get-flights` tool (same data)
✅ Unique `search-flights` widget (re-invokable by LLM)

### Widget handles its own state

Cart, selections, and form inputs live in the widget -- not as tools.

❌ `add-to-cart` tool, `select-seat` tool (these are widget state)
✅ Widget manages state internally. Tools are for backend operations only: `create-checkout`, `submit-order`

### Don't lazy-load

Tool calls are expensive. Return all needed data upfront.

❌ `search-flights` widget + `get-flight-details` tool (lazy-loading)
✅ `search-flights` widget returns full flight data including details

## API Design Pattern

### Flow NEEDS UI -> Widget + Optional Tool(s)

**Example: Flight Booking**

```typescript
// Widget: search-flights
server.tool(
  {
    name: "search-flights",
    schema: z.object({
      destination: z.string().describe("Destination city"),
      dates: z.string().describe("Travel dates"),
    }),
    widget: {
      name: "flight-search",
      invoking: "Searching...",
      invoked: "Flights found",
    },
  },
  async ({ destination, dates }) => {
    const flights = await fetchFlights(destination, dates);
    return widget({
      props: { flights, destination },
      output: text(`Found ${flights.length} flights to ${destination}`),
    });
  },
);

// Tool: create-checkout (called by widget)
server.tool(
  {
    name: "create-checkout",
    schema: z.object({
      flightId: z.string().describe("Selected flight ID"),
      passengers: z.array(z.object({ name: z.string(), email: z.string() })),
    }),
  },
  async ({ flightId, passengers }) => {
    const checkout = await createCheckoutSession(flightId, passengers);
    return object({ checkoutUrl: checkout.url });
  },
);
```

### Flow DOES NOT NEED UI -> Tool(s) Only

**Example: Manage Bookings**

```typescript
// Tool: list-bookings
server.tool(
  {
    name: "list-bookings",
    schema: z.object({ email: z.string().describe("Booking email") }),
  },
  async ({ email }) => {
    const bookings = await getBookings(email);
    return object({ bookings });
    // LLM: "You have two flights: Paris Jan 1, Tokyo Feb 15. Which cancel?"
  },
);

// Tool: cancel-booking
server.tool(
  {
    name: "cancel-booking",
    schema: z.object({
      bookingId: z.string().describe("Booking ID to cancel"),
    }),
  },
  async ({ bookingId }) => {
    await cancelBooking(bookingId);
    return text(`Booking ${bookingId} has been cancelled.`);
  },
);
```

## `exposeAsTool` Defaults to `false`

Widgets are not auto-registered as tools by default. When you define a custom tool with `widget: { name }`, omitting `exposeAsTool` in the widget file is the correct setup:

```typescript
// resources/flight-search.tsx
export const widgetMetadata: WidgetMetadata = {
  description: "Flight search results",
  props: z.object({ flights: z.array(...), destination: z.string() }),
  // exposeAsTool defaults to false — custom tool in index.ts handles registration
};
```

## Review Checklist

Before proceeding to implementation:

- [ ] Every flow has clear tool/widget assignments
- [ ] No duplicate data fetching between widgets and tools
- [ ] Widget state stays in the widget (not separate tools)
- [ ] All data returned upfront (no lazy-loading)
- [ ] Tool names start with verbs
- [ ] One widget per flow
