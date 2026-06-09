"use client";

import { useRef, useCallback, useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { KnowledgeNode, KnowledgeEdge } from "@/lib/types";
import { Network } from "lucide-react";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

const TYPE_COLORS: Record<string, string> = {
  entity: "#3b82f6",
  concept: "#8b5cf6",
  theme: "#ec4899",
  document: "#6b7280",
  module: "#f59e0b",
  class: "#10b981",
  function: "#06b6d4",
  variable: "#f97316",
};

interface KnowledgeGraphProps {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  selectedNodeId: string | null;
  onNodeClick: (nodeId: string) => void;
  onNodeDoubleClick: (nodeId: string) => void;
}

interface GraphNode {
  id: string;
  label: string;
  type: string;
  color: string;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
  weight: number;
}

export function KnowledgeGraph({
  nodes,
  edges,
  selectedNodeId,
  onNodeClick,
  onNodeDoubleClick,
}: KnowledgeGraphProps) {
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force("charge")?.strength(-200);
      fgRef.current.d3Force("link")?.distance(80);
    }
  }, [nodes]);

  const graphData = useMemo(
    () => ({
      nodes: nodes.map((n) => {
        const connectionCount = edges.filter(
          (e) => e.source === n.id || e.target === n.id,
        ).length;
        return {
          id: n.id,
          label: n.label,
          type: n.type,
          color: TYPE_COLORS[n.type] || "#6b7280",
          val: Math.max(2, connectionCount + 1),
        } satisfies GraphNode;
      }),
      links: edges.map((e) => ({
        source: e.source,
        target: e.target,
        label: e.label,
        weight: e.weight,
      })),
    }),
    [nodes, edges],
  );

  const handleNodeClick = useCallback(
    (node: any) => {
      onNodeClick(node.id);
    },
    [onNodeClick],
  );

  const lastClickTime = useRef(0);
  const lastClickNode = useRef<string | null>(null);

  const handleClick = useCallback(
    (node: any) => {
      const now = Date.now();
      if (
        lastClickNode.current === node.id &&
        now - lastClickTime.current < 400
      ) {
        onNodeDoubleClick(node.id);
        lastClickTime.current = 0;
        lastClickNode.current = null;
      } else {
        onNodeClick(node.id);
        lastClickTime.current = now;
        lastClickNode.current = node.id;
      }
    },
    [onNodeClick, onNodeDoubleClick],
  );

  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label;
      const fontSize = 12 / globalScale;
      const nodeSize = Math.sqrt(node.val) * 4;
      const isSelected = node.id === selectedNodeId;

      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, nodeSize + 5, 0, 2 * Math.PI);
        ctx.fillStyle = `${node.color}22`;
        ctx.fill();
        ctx.strokeStyle = node.color;
        ctx.lineWidth = 2 / globalScale;
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
      ctx.fillStyle = node.color;
      ctx.fill();

      ctx.font = `500 ${fontSize}px "Plus Jakarta Sans", sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = document.documentElement.classList.contains("dark")
        ? "#ffffffcc"
        : "#010507cc";
      ctx.fillText(label, node.x, node.y + nodeSize + 4);
    },
    [selectedNodeId],
  );

  const linkCanvasObject = useCallback(
    (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const start = link.source;
      const end = link.target;
      if (!start.x || !end.x) return;

      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.strokeStyle = document.documentElement.classList.contains("dark")
        ? "#ffffff18"
        : "#00000015";
      ctx.lineWidth = Math.max(0.5, (link.weight || 1) * 0.8) / globalScale;
      ctx.stroke();

      if (globalScale > 0.8) {
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;
        const fontSize = 8 / globalScale;
        ctx.font = `${fontSize}px "Plus Jakarta Sans", sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = document.documentElement.classList.contains("dark")
          ? "#adadb2"
          : "#57575b";
        ctx.fillText(link.label || "", midX, midY);
      }
    },
    [],
  );

  return (
    <div ref={containerRef} className="h-full w-full">
      {nodes.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-2 text-[var(--muted-foreground)]">
          <Network className="h-8 w-8 opacity-20" />
          <p className="text-sm">Your knowledge graph will appear here</p>
        </div>
      ) : (
        <ForceGraph2D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeCanvasObject={nodeCanvasObject}
          linkCanvasObject={linkCanvasObject}
          onNodeClick={handleClick}
          nodePointerAreaPaint={(node: any, color, ctx) => {
            const nodeSize = Math.sqrt(node.val) * 4;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, nodeSize + 6, 0, 2 * Math.PI);
            ctx.fill();
          }}
          d3AlphaDecay={0.05}
          d3VelocityDecay={0.4}
          cooldownTicks={100}
          backgroundColor="transparent"
          linkDirectionalParticles={0}
          dagMode={undefined}
          warmupTicks={50}
        />
      )}
    </div>
  );
}
