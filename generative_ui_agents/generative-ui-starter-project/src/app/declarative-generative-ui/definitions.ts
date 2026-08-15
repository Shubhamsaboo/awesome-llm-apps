/**
 * Demonstration Catalog — Component Definitions
 *
 * Platform-agnostic definitions: component names, props (Zod), descriptions.
 * This is the contract between the app and the AI agent. Agents receive these
 * definitions as context so they know what components are available.
 *
 * Renderers (React, React Native, etc.) import these definitions and provide
 * platform-specific implementations, type-checked against the Zod schemas.
 */

import { z } from "zod";

/**
 * Dynamic string: accepts either a literal string or a data-model path binding
 * like `{ path: "airline" }`. The GenericBinder resolves path bindings to the
 * actual value at render time.
 */
const DynString = z.union([z.string(), z.object({ path: z.string() })]);

export const demonstrationCatalogDefinitions = {
  Title: {
    description: "A heading. Use for section titles and page headers.",
    props: z.object({
      text: z.string(),
      level: z.string().optional(),
    }),
  },

  // Text: removed — the basic catalog's Text uses DynamicStringSchema
  // which supports path bindings (e.g. { path: "flights[*].airline" }).
  // Overriding it with z.string() breaks fixed-schema data binding.

  Row: {
    description: "Horizontal layout container.",
    props: z.object({
      gap: z.number().optional(),
      align: z.string().optional(),
      justify: z.string().optional(),
      // Union with { componentId, path } so GenericBinder treats this as
      // STRUCTURAL and resolves template children from the data model.
      children: z.union([
        z.array(z.string()),
        z.object({ componentId: z.string(), path: z.string() }),
      ]),
    }),
  },

  Column: {
    description: "Vertical layout container.",
    props: z.object({
      gap: z.number().optional(),
      align: z.string().optional(),
      // Same union as Row — required for template children support.
      children: z.union([
        z.array(z.string()),
        z.object({ componentId: z.string(), path: z.string() }),
      ]),
    }),
  },

  DashboardCard: {
    description:
      "A card container with title and optional subtitle. Has a 'child' slot for content (chart, metrics, etc). Use 'child' with a single component ID.",
    props: z.object({
      title: z.string(),
      subtitle: z.string().optional(),
      child: z.string().optional(),
    }),
  },

  Metric: {
    description:
      "A key metric display with label, value, and optional trend indicator. Great for KPIs and stats.",
    props: z.object({
      label: z.string(),
      value: z.string(),
      trend: z.enum(["up", "down", "neutral"]).optional(),
      trendValue: z.string().optional(),
    }),
  },

  PieChart: {
    description:
      "A pie/donut chart. Provide data as array of {label, value, color} objects.",
    props: z.object({
      data: z.array(
        z.object({
          label: z.string(),
          value: z.number(),
          color: z.string().optional(),
        }),
      ),
      innerRadius: z.number().optional(),
    }),
  },

  BarChart: {
    description:
      "A bar chart. Provide data as array of {label, value} objects.",
    props: z.object({
      data: z.array(z.object({ label: z.string(), value: z.number() })),
      color: z.string().optional(),
    }),
  },

  Badge: {
    description:
      "A small status badge/tag. Use for labels, statuses, categories.",
    props: z.object({
      text: z.string(),
      variant: z
        .enum(["success", "warning", "error", "info", "neutral"])
        .optional(),
    }),
  },

  DataTable: {
    description: "A data table with columns and rows.",
    props: z.object({
      columns: z.array(z.object({ key: z.string(), label: z.string() })),
      rows: z.array(z.record(z.any())),
    }),
  },

  Button: {
    description:
      "An interactive button with an action event. Use 'child' with a Text component ID for the label. 'action' is dispatched on click.",
    props: z.object({
      child: z
        .string()
        .describe(
          "The ID of the child component (e.g. a Text component for the label).",
        ),
      variant: z.enum(["primary", "secondary", "ghost"]).optional(),
      // Union with { event } so GenericBinder resolves this as ACTION → callable () => void.
      action: z
        .union([
          z.object({
            event: z.object({
              name: z.string(),
              context: z.record(z.any()).optional(),
            }),
          }),
          z.null(),
        ])
        .optional(),
    }),
  },

  FlightCard: {
    description:
      "A rich flight result card. Displays airline, flight number, route, times, duration, status, and price. Use inside a Row for side-by-side layout.",
    props: z.object({
      airline: DynString,
      airlineLogo: DynString,
      flightNumber: DynString,
      origin: DynString,
      destination: DynString,
      date: DynString,
      departureTime: DynString,
      arrivalTime: DynString,
      duration: DynString,
      status: DynString,
      statusColor: DynString.optional(),
      price: DynString,
      action: z
        .union([
          z.object({
            event: z.object({
              name: z.string(),
              context: z.record(z.any()).optional(),
            }),
          }),
          z.null(),
        ])
        .optional(),
    }),
  },
};

/** Type helper for renderers */
export type DemonstrationCatalogDefinitions =
  typeof demonstrationCatalogDefinitions;
