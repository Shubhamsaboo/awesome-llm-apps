/**
 * Build the mcp-use-server E2B sandbox template (production).
 *
 * Run:  npx tsx build.prod.ts
 *
 * Publishes as "mcp-use-server". Copy the resulting template ID into
 * E2B_TEMPLATE in your .env.
 */

import "dotenv/config";
import { Template, defaultBuildLogger } from "e2b";
import { template } from "./template";

async function main() {
  const result = await Template.build(template, "mcp-use-server", {
    cpuCount: 2,
    memoryMB: 2048,
    onBuildLogs: defaultBuildLogger(),
  });
  console.log("\n✓ Template built:", result);
  console.log(
    `  Set E2B_TEMPLATE=${result.templateId} in your .env (template name: ${result.name})`,
  );
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
