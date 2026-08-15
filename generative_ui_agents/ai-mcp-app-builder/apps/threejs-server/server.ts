/**
 * Three.js MCP Server
 *
 * Provides tools for rendering interactive 3D scenes using Three.js.
 */
import {
  RESOURCE_MIME_TYPE,
  registerAppResource,
  registerAppTool,
} from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { ReadResourceResult } from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs/promises";
import path from "node:path";
import { z } from "zod";
import { startServer } from "./server-utils.js";

// =============================================================================
// Constants
// =============================================================================

const DIST_DIR = path.join(import.meta.dirname, "dist");

// Default code example for the Three.js widget
const DEFAULT_THREEJS_CODE = `const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(width, height);
renderer.setClearColor(0x1a1a2e);

const cube = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0x00ff88 })
);
scene.add(cube);

scene.add(new THREE.DirectionalLight(0xffffff, 1));
scene.add(new THREE.AmbientLight(0x404040));

camera.position.z = 3;

function animate() {
  requestAnimationFrame(animate);
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
}
animate();`;

const THREEJS_DOCUMENTATION = `# Three.js Widget Documentation

## Available Globals
- \`THREE\` - Three.js library (r181)
- \`canvas\` - Pre-created canvas element
- \`width\`, \`height\` - Canvas dimensions in pixels
- \`OrbitControls\` - Interactive camera controls
- \`EffectComposer\`, \`RenderPass\`, \`UnrealBloomPass\` - Post-processing effects

## Basic Template
\`\`\`javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(width, height);
renderer.setClearColor(0x1a1a2e);  // Dark background

// Add objects here...

camera.position.z = 5;
renderer.render(scene, camera);  // Static render
\`\`\`

## Example: Rotating Cube with Lighting
\`\`\`javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(width, height);
renderer.setClearColor(0x1a1a2e);

const cube = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0x00ff88 })
);
scene.add(cube);

// Lighting - keep intensity at 1 or below
scene.add(new THREE.DirectionalLight(0xffffff, 1));
scene.add(new THREE.AmbientLight(0x404040));

camera.position.z = 3;

function animate() {
  requestAnimationFrame(animate);
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
}
animate();
\`\`\`

## Example: Interactive OrbitControls
\`\`\`javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(width, height);
renderer.setClearColor(0x2d2d44);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const sphere = new THREE.Mesh(
  new THREE.SphereGeometry(1, 32, 32),
  new THREE.MeshStandardMaterial({ color: 0xff6b6b, roughness: 0.4 })
);
scene.add(sphere);

scene.add(new THREE.DirectionalLight(0xffffff, 1));
scene.add(new THREE.AmbientLight(0x404040));

camera.position.z = 4;

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
\`\`\`

## Tips
- Always set \`renderer.setClearColor()\` to a dark color
- Keep light intensity ≤ 1 to avoid washed-out scenes
- Use \`MeshStandardMaterial\` for realistic lighting
- For animations, use \`requestAnimationFrame\`
`;

const resourceUri = "ui://threejs/mcp-app.html";

// =============================================================================
// Server Setup
// =============================================================================

/**
 * Creates a new MCP server instance with tools and resources registered.
 * Each HTTP session needs its own server instance because McpServer only supports one transport.
 */
export function createServer(): McpServer {
  const server = new McpServer({
    name: "Three.js Server",
    version: "1.0.0",
  });

  // Tool 1: show_threejs_scene
  registerAppTool(
    server,
    "show_threejs_scene",
    {
      title: "Show Three.js Scene",
      description:
        "Render an interactive 3D scene with custom Three.js code. Available globals: THREE, OrbitControls, EffectComposer, RenderPass, UnrealBloomPass, canvas, width, height.",
      inputSchema: {
        code: z
          .string()
          .default(DEFAULT_THREEJS_CODE)
          .describe("JavaScript code to render the 3D scene"),
        height: z
          .number()
          .int()
          .positive()
          .default(400)
          .describe("Height in pixels"),
      },
      outputSchema: z.object({
        code: z.string(),
        height: z.number(),
      }),
      _meta: { ui: { resourceUri } },
    },
    async ({ code, height }) => {
      const data = { code, height };
      return {
        content: [{ type: "text", text: JSON.stringify(data) }],
        structuredContent: data,
      };
    },
  );

  // Tool 2: learn_threejs (not a UI tool, just returns documentation)
  server.registerTool(
    "learn_threejs",
    {
      title: "Learn Three.js",
      description:
        "Get documentation and examples for using the Three.js widget",
      inputSchema: {},
    },
    async () => {
      return {
        content: [{ type: "text", text: THREEJS_DOCUMENTATION }],
      };
    },
  );

  // Resource registration
  registerAppResource(
    server,
    resourceUri,
    resourceUri,
    { mimeType: RESOURCE_MIME_TYPE, description: "Three.js Widget UI" },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(
        path.join(DIST_DIR, "mcp-app.html"),
        "utf-8",
      );

      return {
        contents: [
          {
            uri: resourceUri,
            mimeType: RESOURCE_MIME_TYPE,
            text: html,
          },
        ],
      };
    },
  );

  return server;
}

async function main() {
  if (process.argv.includes("--stdio")) {
    await createServer().connect(new StdioServerTransport());
  } else {
    const port = parseInt(process.env.PORT ?? "3108", 10);
    await startServer(createServer, { port, name: "Three.js Server" });
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
