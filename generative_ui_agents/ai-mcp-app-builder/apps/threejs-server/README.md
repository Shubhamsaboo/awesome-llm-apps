# Example: Three.js App

![Screenshot](screenshot.png)

Interactive 3D scene renderer using Three.js. Demonstrates streaming code preview and full MCP App integration.

## Features

- **Interactive 3D Rendering**: Execute JavaScript code to create and animate Three.js scenes
- **Streaming Preview**: See the scene build in real-time as code is being written
- **Built-in Helpers**: Pre-configured `OrbitControls`, post-processing effects (bloom), and render passes
- **Documentation Tool**: `learn_threejs` provides API docs and code examples on demand

## Running

1. Install dependencies:

   ```bash
   npm install
   ```

2. Build and start the server:

   ```bash
   npm run start:http  # for Streamable HTTP transport
   # OR
   npm run start:stdio  # for stdio transport
   ```

3. View using the [`basic-host`](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-host) example or another MCP Apps-compatible host.

### Tool Input

To test the example, copy the contents of [`test-input.json`](test-input.json) into the tool input field in `basic-host`.

The test input creates a simple scene with a rotating cube:

```javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100);
camera.position.set(2, 2, 2);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(width, height);
renderer.shadowMap.enabled = true;

const cube = new THREE.Mesh(
  new THREE.BoxGeometry(),
  new THREE.MeshStandardMaterial({ color: 0x00ff88 }),
);
cube.castShadow = true;
cube.position.y = 0.5;
scene.add(cube);

const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(5, 5),
  new THREE.MeshStandardMaterial({ color: 0x222233 }),
);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

const light = new THREE.DirectionalLight(0xffffff, 2);
light.position.set(3, 5, 3);
light.castShadow = true;
scene.add(light);
scene.add(new THREE.AmbientLight(0x404040));

function animate() {
  requestAnimationFrame(animate);
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
}
animate();
```

#### Available Three.js Globals

When writing custom code, these globals are available:

```javascript
THREE; // Three.js library
canvas; // Pre-created canvas element
width; // Canvas width
height; // Canvas height
OrbitControls; // Camera controls
EffectComposer; // Post-processing composer
RenderPass; // Render pass
UnrealBloomPass; // Bloom effect
```

## Architecture

### Server (`server.ts`)

Exposes two tools:

- `show_threejs_scene` - Renders a 3D scene from JavaScript code
- `learn_threejs` - Returns documentation and code examples for Three.js APIs

Supports Streamable HTTP and stdio transports.

### App (`src/threejs-app.tsx`)

React component that:

- Receives tool inputs via the MCP App SDK
- Displays streaming preview from `toolInputsPartial.code` as code arrives
- Executes final code from `toolInputs.code` when complete
- Renders to a pre-created canvas with configurable height
