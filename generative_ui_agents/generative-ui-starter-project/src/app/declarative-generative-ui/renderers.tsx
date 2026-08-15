/**
 * A2UI Catalog — React Renderers
 *
 * Each renderer maps a component name from definitions.ts to a React
 * implementation. Props are type-checked against the Zod schemas.
 *
 * To add a component: define its schema in definitions.ts, then add a
 * renderer here. See README.md "Adding a custom component" for details.
 *
 * The assembled catalog is registered in layout.tsx via
 * <CopilotKit a2ui={{ catalog: demonstrationCatalog }}>.
 */
"use client";

import React, { useState } from "react";
import {
  PieChart as RechartsPie,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart as RechartsBar,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  createCatalog,
  type CatalogRenderers,
} from "@copilotkit/a2ui-renderer";
import {
  demonstrationCatalogDefinitions,
  type DemonstrationCatalogDefinitions,
} from "./definitions";

// ─── Theme-aware colors ─────────────────────────────────────────────

const c = {
  card: "var(--card)",
  cardFg: "var(--card-foreground)",
  border: "var(--border)",
  muted: "var(--muted-foreground)",
  divider: "color-mix(in srgb, var(--border) 50%, var(--card))",
  shadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
  btnBg: "color-mix(in srgb, var(--muted) 40%, var(--card))",
  btnDoneBg: "color-mix(in srgb, #22c55e 10%, var(--card))",
};

function ActionButton({
  label,
  doneLabel,
  action,
  children: child,
}: {
  label: string;
  doneLabel: string;
  action: any;
  children?: React.ReactNode;
}) {
  const [done, setDone] = useState(false);
  return (
    <button
      disabled={done}
      style={{
        width: "100%",
        padding: "10px 16px",
        borderRadius: "10px",
        border: done ? "1px solid #bbf7d0" : `1px solid ${c.border}`,
        background: done ? c.btnDoneBg : c.btnBg,
        color: done ? "#059669" : c.cardFg,
        fontSize: "0.85rem",
        fontWeight: 500,
        cursor: done ? "default" : "pointer",
        transition: "all 0.2s ease",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "6px",
      }}
      onClick={() => {
        if (!done) {
          action?.();
          setDone(true);
        }
      }}
    >
      {done && (
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#059669"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      )}
      {done ? doneLabel : (child ?? label)}
    </button>
  );
}

// ─── Renderers (type-checked against schema definitions) ────────────

const demonstrationCatalogRenderers: CatalogRenderers<DemonstrationCatalogDefinitions> =
  {
    Title: ({ props }) => {
      const Tag = (
        props.level === "h1" ? "h1" : props.level === "h3" ? "h3" : "h2"
      ) as keyof JSX.IntrinsicElements;
      const sizes: Record<string, string> = {
        h1: "1.75rem",
        h2: "1.25rem",
        h3: "1rem",
      };
      return (
        <Tag
          style={{
            margin: 0,
            fontWeight: 600,
            fontSize: sizes[props.level ?? "h2"],
            color: c.cardFg,
            letterSpacing: "-0.01em",
          }}
        >
          {props.text}
        </Tag>
      );
    },

    // Text: removed — use the basic catalog's Text (supports DynamicStringSchema
    // for path bindings in fixed-schema templates).

    Row: ({ props, children }) => {
      const justifyMap: Record<string, string> = {
        start: "flex-start",
        center: "center",
        end: "flex-end",
        spaceBetween: "space-between",
      };
      const items = Array.isArray(props.children) ? props.children : [];
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            gap: `${props.gap ?? 16}px`,
            alignItems: props.align ?? "stretch",
            justifyContent:
              justifyMap[props.justify ?? "start"] ?? "flex-start",
            flexWrap: "wrap",
            width: "100%",
          }}
        >
          {items.map((item: any, i: number) => {
            if (typeof item === "string")
              return (
                <div
                  key={`${item}-${i}`}
                  style={{ flex: "1 1 0", minWidth: 0 }}
                >
                  {children(item)}
                </div>
              );
            if (item && typeof item === "object" && "id" in item)
              return (
                <div
                  key={`${item.id}-${i}`}
                  style={{ flex: "1 1 0", minWidth: 0 }}
                >
                  {(children as any)(item.id, item.basePath)}
                </div>
              );
            return null;
          })}
        </div>
      );
    },

    Column: ({ props, children }) => {
      const items = Array.isArray(props.children) ? props.children : [];
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: `${props.gap ?? 12}px`,
            width: "100%",
          }}
        >
          {items.map((item: any, i: number) => {
            if (typeof item === "string")
              return (
                <React.Fragment key={`${item}-${i}`}>
                  {children(item)}
                </React.Fragment>
              );
            if (item && typeof item === "object" && "id" in item)
              return (
                <React.Fragment key={`${item.id}-${i}`}>
                  {(children as any)(item.id, item.basePath)}
                </React.Fragment>
              );
            return null;
          })}
        </div>
      );
    },

    DashboardCard: ({ props, children }) => (
      <div
        style={{
          background: c.card,
          borderRadius: "12px",
          border: `1px solid ${c.border}`,
          padding: "20px",
          boxShadow: c.shadow,
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.9rem", color: c.cardFg }}>
            {props.title}
          </div>
          {props.subtitle && (
            <div
              style={{
                fontSize: "0.75rem",
                color: c.muted,
                marginTop: "2px",
              }}
            >
              {props.subtitle}
            </div>
          )}
        </div>
        {props.child && children(props.child)}
      </div>
    ),

    Metric: ({ props }) => {
      const trendColors: Record<string, string> = {
        up: "#059669",
        down: "#dc2626",
        neutral: c.muted,
      };
      const trendIcons: Record<string, string> = {
        up: "↑",
        down: "↓",
        neutral: "→",
      };
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <span
            style={{
              fontSize: "0.75rem",
              color: c.muted,
              fontWeight: 500,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            {props.label}
          </span>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: c.cardFg,
                letterSpacing: "-0.02em",
              }}
            >
              {props.value}
            </span>
            {props.trend && props.trendValue && (
              <span
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 500,
                  color: trendColors[props.trend] ?? c.muted,
                }}
              >
                {trendIcons[props.trend]} {props.trendValue}
              </span>
            )}
          </div>
        </div>
      );
    },

    PieChart: ({ props }) => {
      const COLORS = [
        "#3b82f6",
        "#8b5cf6",
        "#ec4899",
        "#f59e0b",
        "#10b981",
        "#6366f1",
      ];
      const data = props.data ?? [];
      return (
        <div style={{ width: "100%", height: 200 }}>
          <ResponsiveContainer>
            <RechartsPie>
              <Pie
                data={data}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                innerRadius={props.innerRadius ?? 40}
                outerRadius={80}
                paddingAngle={2}
              >
                {data.map((entry: any, i: number) => (
                  <Cell
                    key={i}
                    fill={entry.color ?? COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </RechartsPie>
          </ResponsiveContainer>
        </div>
      );
    },

    BarChart: ({ props }) => {
      const data = props.data ?? [];
      return (
        <div style={{ width: "100%", height: 200 }}>
          <ResponsiveContainer>
            <RechartsBar data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke={c.divider} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: c.muted }} />
              <YAxis tick={{ fontSize: 11, fill: c.muted }} />
              <Tooltip />
              <Bar
                dataKey="value"
                fill={props.color ?? "#3b82f6"}
                radius={[4, 4, 0, 0]}
              />
            </RechartsBar>
          </ResponsiveContainer>
        </div>
      );
    },

    Badge: ({ props }) => {
      const variants: Record<string, { bg: string; color: string }> = {
        success: { bg: "#dcfce7", color: "#166534" },
        warning: { bg: "#fef3c7", color: "#92400e" },
        error: { bg: "#fee2e2", color: "#991b1b" },
        info: { bg: "#dbeafe", color: "#1e40af" },
        neutral: { bg: "var(--muted)", color: c.cardFg },
      };
      const v = variants[props.variant ?? "neutral"] ?? variants.neutral;
      return (
        <span
          style={{
            display: "inline-block",
            padding: "2px 8px",
            borderRadius: "9999px",
            fontSize: "0.7rem",
            fontWeight: 500,
            background: v.bg,
            color: v.color,
          }}
        >
          {props.text}
        </span>
      );
    },

    DataTable: ({ props }) => {
      const cols = props.columns ?? [];
      const rows = props.rows ?? [];
      return (
        <div style={{ overflowX: "auto", width: "100%" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "0.8rem",
            }}
          >
            <thead>
              <tr>
                {cols.map((col: any) => (
                  <th
                    key={col.key}
                    style={{
                      textAlign: "left",
                      padding: "8px 12px",
                      borderBottom: `2px solid ${c.border}`,
                      color: c.muted,
                      fontWeight: 600,
                      fontSize: "0.7rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row: any, i: number) => (
                <tr key={i} style={{ borderBottom: `1px solid ${c.divider}` }}>
                  {cols.map((col: any) => (
                    <td
                      key={col.key}
                      style={{ padding: "8px 12px", color: c.cardFg }}
                    >
                      {String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    },

    Button: ({ props, children }) => {
      return (
        <ActionButton label="Click" doneLabel="Done" action={props.action}>
          {props.child ? children(props.child) : null}
        </ActionButton>
      );
    },

    FlightCard: ({ props: rawProps }) => {
      // The binder resolves path bindings to strings at runtime.
      const props = rawProps as Record<string, any>;
      const statusColors: Record<string, string> = {
        "On Time": "#22c55e",
        Delayed: "#eab308",
        Cancelled: "#ef4444",
      };
      const dotColor =
        props.statusColor ?? statusColors[props.status] ?? "#22c55e";

      return (
        <div
          style={{
            border: `1px solid ${c.border}`,
            borderRadius: "16px",
            padding: "20px",
            background: c.card,
            color: c.cardFg,
            minWidth: 260,
            maxWidth: 340,
            flex: "1 1 260px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            boxShadow: c.shadow,
          }}
        >
          {/* Header: airline + price */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <img
                src={props.airlineLogo}
                alt={props.airline}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  objectFit: "contain",
                }}
              />
              <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                {props.airline}
              </span>
            </div>
            <span style={{ fontWeight: 700, fontSize: "1.15rem" }}>
              {props.price}
            </span>
          </div>

          {/* Meta */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "0.8rem",
              color: c.muted,
            }}
          >
            <span>{props.flightNumber}</span>
            <span>{props.date}</span>
          </div>

          <hr
            style={{
              border: "none",
              borderTop: `1px solid ${c.divider}`,
              margin: 0,
            }}
          />

          {/* Times */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontWeight: 700, fontSize: "1.1rem" }}>
              {props.departureTime}
            </span>
            <span style={{ fontSize: "0.75rem", color: c.muted }}>
              {props.duration}
            </span>
            <span style={{ fontWeight: 700, fontSize: "1.1rem" }}>
              {props.arrivalTime}
            </span>
          </div>

          {/* Route */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "0.95rem",
              fontWeight: 600,
            }}
          >
            <span>{props.origin}</span>
            <span style={{ color: c.muted }}>→</span>
            <span>{props.destination}</span>
          </div>

          <div
            style={{
              marginTop: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <hr
              style={{
                border: "none",
                borderTop: `1px solid ${c.divider}`,
                margin: 0,
              }}
            />

            {/* Status */}
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: dotColor,
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: "0.8rem", color: c.muted }}>
                {props.status}
              </span>
            </div>

            <ActionButton
              label="Select"
              doneLabel="Selected"
              action={props.action}
            />
          </div>
        </div>
      );
    },
  };

// ─── Assembled Catalog ───────────────────────────────────────────────

export const demonstrationCatalog = createCatalog(
  demonstrationCatalogDefinitions,
  demonstrationCatalogRenderers,
  {
    catalogId: "copilotkit://app-dashboard-catalog",
  },
);
