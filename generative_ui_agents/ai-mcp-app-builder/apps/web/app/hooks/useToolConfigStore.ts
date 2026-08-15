"use client";

import { useCallback, useEffect, useMemo } from "react";
import { useLocalStorage } from "./useLocalStorage";
import type { IntrospectedTool } from "./useMcpIntrospect";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Locally stored tool configuration — supports overrides and brand-new tools */
export interface LocalToolConfig {
  toolName: string;
  source: "introspected" | "local";
  description: string;
  inputSchema: Record<string, unknown>;
  htmlSource: string | null;
  previewData: Record<string, unknown>;
  serverEndpoint?: string;
  createdAt: number;
  updatedAt: number;
}

/** Merged view shown in the UI: introspected data + local overrides */
export interface MergedToolConfig {
  toolName: string;
  source: "introspected" | "local";
  description: string;
  inputSchema: Record<string, unknown>;
  htmlSource: string | null;
  previewData: Record<string, unknown>;
  hasUI: boolean;
  uiResourceUri: string | null;
  _meta: Record<string, unknown> | null;
  isModified: boolean;
}

// ---------------------------------------------------------------------------
// Mock data generator
// ---------------------------------------------------------------------------

export function generatePreviewData(
  inputSchema: Record<string, unknown>,
): Record<string, unknown> {
  const props = inputSchema?.properties as
    | Record<
        string,
        {
          type?: string;
          description?: string;
          enum?: string[];
          default?: unknown;
        }
      >
    | undefined;
  if (!props) return {};
  const mock: Record<string, unknown> = {};
  for (const [key, schema] of Object.entries(props)) {
    if (schema.default !== undefined) {
      mock[key] = schema.default;
    } else if (schema.enum && schema.enum.length > 0) {
      mock[key] = schema.enum[0];
    } else {
      switch (schema.type) {
        case "string":
          mock[key] = schema.description
            ? schema.description.slice(0, 80)
            : `sample_${key}`;
          break;
        case "number":
        case "integer":
          mock[key] = 42;
          break;
        case "boolean":
          mock[key] = true;
          break;
        case "array":
          mock[key] = [];
          break;
        case "object":
          mock[key] = {};
          break;
        default:
          mock[key] = `sample_${key}`;
      }
    }
  }
  return mock;
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

export interface ValidationResult {
  test: string;
  passed: boolean;
  message: string;
}

export function validateToolConfig(config: MergedToolConfig): {
  summary: string;
  results: ValidationResult[];
  allPassed: boolean;
} {
  const results: ValidationResult[] = [];

  // 1. Schema structure
  const schema = config.inputSchema;
  if (!schema || typeof schema !== "object") {
    results.push({
      test: "Schema structure",
      passed: false,
      message: "Schema is not a valid object",
    });
  } else if (
    !(schema as Record<string, unknown>).properties &&
    !(schema as Record<string, unknown>).type
  ) {
    results.push({
      test: "Schema structure",
      passed: false,
      message: "Schema missing 'type' or 'properties'",
    });
  } else {
    results.push({
      test: "Schema structure",
      passed: true,
      message: "Valid JSON Schema structure",
    });
  }

  // 2. Mock data completeness
  const required =
    ((schema as Record<string, unknown>)?.required as string[]) ?? [];
  const mockKeys = Object.keys(config.previewData);
  const missingRequired = required.filter((r) => !mockKeys.includes(r));
  if (missingRequired.length > 0) {
    results.push({
      test: "Mock data completeness",
      passed: false,
      message: `Missing required fields: ${missingRequired.join(", ")}`,
    });
  } else {
    results.push({
      test: "Mock data completeness",
      passed: true,
      message: `All ${required.length} required fields present`,
    });
  }

  // 3. Mock data type matching
  const props =
    ((schema as Record<string, unknown>)?.properties as Record<
      string,
      { type?: string }
    >) ?? {};
  let typeErrors = 0;
  for (const [key, value] of Object.entries(config.previewData)) {
    const propSchema = props[key];
    if (propSchema?.type) {
      const actualType = Array.isArray(value) ? "array" : typeof value;
      const expectedType =
        propSchema.type === "integer" ? "number" : propSchema.type;
      if (actualType !== expectedType) {
        typeErrors++;
      }
    }
  }
  results.push({
    test: "Mock data types",
    passed: typeErrors === 0,
    message:
      typeErrors === 0
        ? "All types match schema"
        : `${typeErrors} type mismatch(es)`,
  });

  // 4. HTML check
  if (config.hasUI || config.htmlSource) {
    if (!config.htmlSource || config.htmlSource.length === 0) {
      results.push({
        test: "UI HTML",
        passed: false,
        message: "HTML source is empty",
      });
    } else if (!config.htmlSource.includes("<script")) {
      results.push({
        test: "UI HTML",
        passed: false,
        message: "HTML has no <script> tags",
      });
    } else {
      results.push({
        test: "UI HTML",
        passed: true,
        message: `Valid HTML (${(config.htmlSource.length / 1024).toFixed(1)} KB)`,
      });
    }
  }

  // 5. Description check
  if (!config.description || config.description.length < 5) {
    results.push({
      test: "Description",
      passed: false,
      message: "Description is too short or missing",
    });
  } else {
    results.push({
      test: "Description",
      passed: true,
      message: "Description looks good",
    });
  }

  const passed = results.filter((r) => r.passed).length;
  return {
    summary: `${passed}/${results.length} checks passed`,
    results,
    allPassed: passed === results.length,
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

const TOOL_CONFIGS_KEY = "mcp-builder-configs";

export function useToolConfigStore(introspectedTools: IntrospectedTool[]) {
  const [configs, setConfigs] = useLocalStorage<
    Record<string, LocalToolConfig>
  >(TOOL_CONFIGS_KEY, {});

  // Auto-populate configs for newly introspected tools AND prune stale ones
  useEffect(() => {
    setConfigs((prev) => {
      const next = { ...prev };
      let changed = false;

      const introspectedNames = new Set(introspectedTools.map((t) => t.name));

      // --- Prune: remove introspected tools no longer present in any connected server ---
      for (const key of Object.keys(next)) {
        if (
          next[key].source === "introspected" &&
          !introspectedNames.has(key)
        ) {
          console.log(
            `[useToolConfigStore] Pruning stale introspected tool "${key}" (no longer in any connected server)`,
          );
          delete next[key];
          changed = true;
        }
      }

      // --- Upsert: add or sync tools currently returned by introspection ---
      for (const tool of introspectedTools) {
        if (!next[tool.name]) {
          console.log(
            `[useToolConfigStore] Adding new introspected tool "${tool.name}"`,
          );
          next[tool.name] = {
            toolName: tool.name,
            source: "introspected",
            description: tool.description,
            inputSchema: tool.inputSchema,
            htmlSource: tool.uiHtml,
            previewData: tool.hasUI
              ? (tool.uiPreviewData ?? {})
              : generatePreviewData(tool.inputSchema),
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          changed = true;
        } else {
          // Migrate: if config has old "mockData" field, move it to "previewData"
          const raw = next[tool.name] as unknown as Record<string, unknown>;
          if (raw.mockData !== undefined && raw.previewData === undefined) {
            next[tool.name] = {
              ...next[tool.name],
              previewData: tool.hasUI
                ? {}
                : (raw.mockData as Record<string, unknown>),
              updatedAt: Date.now(),
            };
            delete (next[tool.name] as unknown as Record<string, unknown>)
              .mockData;
            changed = true;
          }
          // Keep HTML in sync from server for non-locally-modified tools
          if (next[tool.name].source === "introspected" && tool.uiHtml) {
            if (next[tool.name].htmlSource !== tool.uiHtml) {
              next[tool.name] = {
                ...next[tool.name],
                htmlSource: tool.uiHtml,
                updatedAt: Date.now(),
              };
              changed = true;
            }
          }
          // Keep previewData in sync when server-defined ui/previewData changes
          if (
            next[tool.name].source === "introspected" &&
            tool.uiPreviewData &&
            JSON.stringify(next[tool.name].previewData) !==
              JSON.stringify(tool.uiPreviewData)
          ) {
            next[tool.name] = {
              ...next[tool.name],
              previewData: tool.uiPreviewData,
              updatedAt: Date.now(),
            };
            changed = true;
          }
        }
      }

      if (!changed) {
        console.log(
          `[useToolConfigStore] Configs in sync — ${Object.keys(next).length} tool(s):`,
          Object.keys(next),
        );
      } else {
        console.log(
          `[useToolConfigStore] Configs updated — ${Object.keys(next).length} tool(s):`,
          Object.keys(next),
        );
      }

      return changed ? next : prev;
    });
  }, [introspectedTools, setConfigs]);

  // Merge introspected + local configs into a unified view
  const mergedTools = useMemo((): MergedToolConfig[] => {
    const result: MergedToolConfig[] = [];
    const seen = new Set<string>();

    const introspectedNames = introspectedTools.map((t) => t.name);
    const configKeys = Object.keys(configs);
    const staleKeys = configKeys.filter(
      (k) =>
        configs[k].source === "introspected" && !introspectedNames.includes(k),
    );
    console.log("[useToolConfigStore] mergedTools recompute", {
      configsCount: configKeys.length,
      configKeys,
      introspectedCount: introspectedTools.length,
      introspectedNames,
      staleIntrospectedKeys: staleKeys,
    });

    for (const config of Object.values(configs)) {
      seen.add(config.toolName);
      const introspected = introspectedTools.find(
        (t) => t.name === config.toolName,
      );
      result.push({
        toolName: config.toolName,
        source: config.source,
        description: config.description,
        inputSchema: config.inputSchema,
        htmlSource: config.htmlSource,
        previewData: config.previewData,
        hasUI: config.htmlSource !== null,
        uiResourceUri: introspected?.uiResourceUri ?? null,
        _meta: introspected?._meta ?? null,
        isModified:
          config.source === "introspected" &&
          !!(
            introspected &&
            (config.description !== introspected.description ||
              JSON.stringify(config.inputSchema) !==
                JSON.stringify(introspected.inputSchema))
          ),
      });
    }

    // Safety: add any introspected tools not yet in configs
    for (const tool of introspectedTools) {
      if (!seen.has(tool.name)) {
        result.push({
          toolName: tool.name,
          source: "introspected",
          description: tool.description,
          inputSchema: tool.inputSchema,
          htmlSource: tool.uiHtml,
          previewData: generatePreviewData(tool.inputSchema),
          hasUI: tool.hasUI,
          uiResourceUri: tool.uiResourceUri,
          _meta: tool._meta,
          isModified: false,
        });
      }
    }

    return result;
  }, [configs, introspectedTools]);

  const getConfig = useCallback(
    (toolName: string): LocalToolConfig | null => configs[toolName] ?? null,
    [configs],
  );

  const getMockData = useCallback(
    (toolName: string): Record<string, unknown> =>
      configs[toolName]?.previewData ?? {},
    [configs],
  );

  const updateConfig = useCallback(
    (
      toolName: string,
      updates: Partial<Omit<LocalToolConfig, "toolName" | "createdAt">>,
    ) => {
      setConfigs((prev) => {
        if (!prev[toolName]) return prev;
        return {
          ...prev,
          [toolName]: { ...prev[toolName], ...updates, updatedAt: Date.now() },
        };
      });
    },
    [setConfigs],
  );

  const createTool = useCallback(
    (
      toolName: string,
      description: string,
      inputSchema: Record<string, unknown>,
    ): LocalToolConfig => {
      const config: LocalToolConfig = {
        toolName,
        source: "local",
        description,
        inputSchema,
        htmlSource: null,
        previewData: generatePreviewData(inputSchema),
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      setConfigs((prev) => ({ ...prev, [toolName]: config }));
      return config;
    },
    [setConfigs],
  );

  const deleteTool = useCallback(
    (toolName: string) => {
      setConfigs((prev) => {
        const next = { ...prev };
        if (next[toolName]?.source === "local") {
          delete next[toolName];
        }
        return next;
      });
    },
    [setConfigs],
  );

  const resetToIntrospected = useCallback(
    (toolName: string) => {
      const introspected = introspectedTools.find((t) => t.name === toolName);
      if (!introspected) return;
      setConfigs((prev) => ({
        ...prev,
        [toolName]: {
          ...prev[toolName],
          description: introspected.description,
          inputSchema: introspected.inputSchema,
          htmlSource: introspected.uiHtml,
          previewData: generatePreviewData(introspected.inputSchema),
          updatedAt: Date.now(),
        },
      }));
    },
    [introspectedTools, setConfigs],
  );

  return {
    configs,
    mergedTools,
    getConfig,
    getMockData,
    updateConfig,
    createTool,
    deleteTool,
    resetToIntrospected,
  };
}
