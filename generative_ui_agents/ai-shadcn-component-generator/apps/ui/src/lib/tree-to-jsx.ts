const COMPONENT_MAP: Record<string, { component: string; path: string }> = {
  card: { component: "Card", path: "@/components/ui/card" },
  row: { component: "Row", path: "@/components/ui/layout" },
  column: { component: "Column", path: "@/components/ui/layout" },
  chart: { component: "SimpleChart", path: "@/components/ui/simple-chart" },
  calendar: { component: "Calendar", path: "@/components/ui/calendar" },
  code_block: { component: "CodeBlock", path: "@/components/ui/code-block" },
  menubar: { component: "Menubar", path: "@/components/ui/menubar" },
  menubar_menu: { component: "MenubarMenu", path: "@/components/ui/menubar" },
  menubar_trigger: { component: "MenubarTrigger", path: "@/components/ui/menubar" },
  menubar_content: { component: "MenubarContent", path: "@/components/ui/menubar" },
  menubar_item: { component: "MenubarItem", path: "@/components/ui/menubar" },
  input: { component: "Input", path: "@/components/ui/input" },
  button: { component: "Button", path: "@/components/ui/button" },
  select: { component: "SimpleSelect", path: "@/components/ui/simple-select" },
  label: { component: "Label", path: "@/components/ui/label" },
};

function formatPropValue(value: unknown): string {
  if (typeof value === "string") return `"${value}"`;
  if (typeof value === "number" || typeof value === "boolean") return `{${value}}`;
  if (Array.isArray(value)) return `{${JSON.stringify(value)}}`;
  if (typeof value === "object" && value !== null) return `{${JSON.stringify(value)}}`;
  return `{${String(value)}}`;
}

function nodeToJsx(node: unknown, indent: number, imports: Set<string>): string {
  if (typeof node === "string") return "  ".repeat(indent) + node;
  if (!node || typeof node !== "object") return "";

  const entries = Object.entries(node as Record<string, unknown>);
  if (entries.length === 0) return "";

  const [tagName, nodeData] = entries[0];
  if (tagName === "markdown") return "";
  if (!nodeData || typeof nodeData !== "object") return "";

  const data = nodeData as Record<string, unknown>;
  const mapping = COMPONENT_MAP[tagName];
  const componentName = mapping?.component ?? tagName;

  if (mapping) {
    imports.add(mapping.path + "|" + mapping.component);
  }

  const propsObj = data.props as Record<string, unknown> | undefined;
  const propValues = (propsObj?.value ?? propsObj?.partialValue ?? {}) as Record<string, unknown>;
  const propsStr = Object.entries(propValues)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([key, val]) => ` ${key}=${formatPropValue(val)}`)
    .join("");

  const pad = "  ".repeat(indent);
  const children = data.children;

  if (!children || (Array.isArray(children) && children.length === 0)) {
    return `${pad}<${componentName}${propsStr} />`;
  }

  if (typeof children === "string") {
    return `${pad}<${componentName}${propsStr}>${children}</${componentName}>`;
  }

  if (Array.isArray(children)) {
    const childJsx = children
      .map((c) => nodeToJsx(c, indent + 1, imports))
      .filter(Boolean)
      .join("\n");
    return `${pad}<${componentName}${propsStr}>\n${childJsx}\n${pad}</${componentName}>`;
  }

  return `${pad}<${componentName}${propsStr} />`;
}

export function treeToJsx(tree: unknown[]): { code: string; importBlock: string } {
  const imports = new Set<string>();

  const jsxLines = tree
    .map((node) => nodeToJsx(node, 2, imports))
    .filter(Boolean)
    .join("\n");

  const importMap = new Map<string, string[]>();
  for (const entry of imports) {
    const [path, component] = entry.split("|");
    if (!importMap.has(path)) importMap.set(path, []);
    importMap.get(path)!.push(component);
  }

  const importBlock = Array.from(importMap.entries())
    .map(([path, components]) => `import { ${components.join(", ")} } from "${path}";`)
    .join("\n");

  const code = importBlock
    ? `${importBlock}\n\nexport default function GeneratedComponent() {\n  return (\n    <>\n${jsxLines}\n    </>\n  );\n}`
    : `export default function GeneratedComponent() {\n  return (\n    <>\n${jsxLines}\n    </>\n  );\n}`;

  return { code, importBlock };
}
