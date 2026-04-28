/**
 * Three.js App Component
 *
 * Renders interactive 3D scenes using Three.js with streaming code preview.
 * Receives all MCP App props from the wrapper.
 */
import { useState, useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import type { WidgetProps } from "./mcp-app-wrapper.tsx";

// =============================================================================
// Types
// =============================================================================

interface ThreeJSToolInput {
  code?: string;
  height?: number;
}

type ThreeJSAppProps = WidgetProps<ThreeJSToolInput>;

// =============================================================================
// Constants
// =============================================================================

// Default demo code shown when no code is provided
const DEFAULT_THREEJS_CODE = `const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(width, height);
renderer.setClearColor(0x1a1a2e);

const cube = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0x00ff88 })
);
// Start with an isometric-ish rotation to show 3 faces
cube.rotation.x = 0.5;
cube.rotation.y = 0.7;
scene.add(cube);

// Better lighting: key light + fill light + ambient
const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
keyLight.position.set(1, 1, 2);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0x8888ff, 0.4);
fillLight.position.set(-1, 0, -1);
scene.add(fillLight);
scene.add(new THREE.AmbientLight(0x404040, 0.5));

camera.position.z = 3;

function animate() {
  requestAnimationFrame(animate);
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
}
animate();`;

// =============================================================================
// Streaming Preview
// =============================================================================

const SHIMMER_STYLE = `
  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
`;

function LoadingShimmer({ height, code }: { height: number; code?: string }) {
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (preRef.current) preRef.current.scrollTop = preRef.current.scrollHeight;
  }, [code]);

  return (
    <div
      style={{
        width: "100%",
        height,
        borderRadius: 8,
        padding: 16,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background:
          "linear-gradient(90deg, #1a1a2e 25%, #2d2d44 50%, #1a1a2e 75%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s ease-in-out infinite",
      }}
    >
      <style>{SHIMMER_STYLE}</style>
      <div
        style={{
          color: "#888",
          fontFamily: "system-ui",
          fontSize: 12,
          marginBottom: 8,
        }}
      >
        🎮 Three.js
      </div>
      {code && (
        <pre
          ref={preRef}
          style={{
            margin: 0,
            padding: 0,
            flex: 1,
            overflow: "auto",
            color: "#aaa",
            fontFamily: "monospace",
            fontSize: 11,
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {code}
        </pre>
      )}
    </div>
  );
}

// =============================================================================
// Three.js Execution
// =============================================================================

const threeContext = {
  THREE,
  OrbitControls,
  EffectComposer,
  RenderPass,
  UnrealBloomPass,
};

async function executeThreeCode(
  code: string,
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
): Promise<void> {
  const fn = new Function(
    "ctx",
    "canvas",
    "width",
    "height",
    `const { THREE, OrbitControls, EffectComposer, RenderPass, UnrealBloomPass } = ctx;
     return (async () => { ${code} })();`,
  );
  await fn(threeContext, canvas, width, height);
}

// =============================================================================
// Main Component
// =============================================================================

export default function ThreeJSApp({
  toolInputs,
  toolInputsPartial,
  toolResult: _toolResult,
  hostContext,
  callServerTool: _callServerTool,
  sendMessage: _sendMessage,
  openLink: _openLink,
  sendLog: _sendLog,
}: ThreeJSAppProps) {
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const height = toolInputs?.height ?? toolInputsPartial?.height ?? 400;
  const code = toolInputs?.code || DEFAULT_THREEJS_CODE;
  const partialCode = toolInputsPartial?.code;
  const isStreaming = !toolInputs && !!toolInputsPartial;

  const safeAreaInsets = hostContext?.safeAreaInsets;
  const containerStyle = {
    paddingTop: safeAreaInsets?.top,
    paddingRight: safeAreaInsets?.right,
    paddingBottom: safeAreaInsets?.bottom,
    paddingLeft: safeAreaInsets?.left,
  };

  useEffect(() => {
    if (!code || !canvasRef.current || !containerRef.current) return;

    setError(null);
    const width = containerRef.current.offsetWidth || 800;
    executeThreeCode(code, canvasRef.current, width, height).catch((e) =>
      setError(e instanceof Error ? e.message : "Unknown error"),
    );
  }, [code, height]);

  if (isStreaming || !code) {
    return (
      <div style={containerStyle}>
        <LoadingShimmer height={height} code={partialCode} />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="threejs-container"
      style={containerStyle}
    >
      <canvas
        id="threejs-canvas"
        ref={canvasRef}
        style={{
          width: "100%",
          height,
          borderRadius: 8,
          display: "block",
          background: "#1a1a2e",
        }}
      />
      {error && <div className="error-overlay">Error: {error}</div>}
    </div>
  );
}
