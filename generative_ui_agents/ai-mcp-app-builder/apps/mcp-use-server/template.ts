/**
 * E2B Sandbox Template Definition — mcp-use-server
 *
 * This bakes the mcp-use-server + all npm dependencies into an E2B image
 * so that Sandbox.create(templateId) starts in seconds with no npm install.
 *
 * Build:
 *   npx tsx build.dev.ts   → publishes as "mcp-use-server-dev"
 *   npx tsx build.prod.ts  → publishes as "mcp-use-server"
 *
 * After building, copy the template ID into E2B_TEMPLATE in your .env.
 */

import { Template, waitForPort } from "e2b";

export const template = Template()
  .fromNodeImage("lts") // Node.js LTS base image
  .setWorkdir("/home/user/workspace")
  .copy(".", "/home/user/workspace") // copy all project files
  .runCmd("npm install --no-audit --no-fund") // bake node_modules into image
  .runCmd("npm run build") // pre-build the mcp-use widgets
  .setStartCmd(
    // start the server when sandbox launches
    "npx tsx index.ts",
    waitForPort(3109), // wait until port 3109 is open
  );
