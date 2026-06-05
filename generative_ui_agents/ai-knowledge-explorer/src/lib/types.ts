export interface KnowledgeNode {
  id: string;
  label: string;
  type:
    | "entity"
    | "concept"
    | "theme"
    | "document"
    | "module"
    | "class"
    | "function"
    | "variable";
  description: string;
  detail: string;
  sourceDocuments: string[];
}

export interface KnowledgeEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  weight: number;
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  content: string;
  status: "uploaded" | "processing" | "extracted";
}

export interface KnowledgeState {
  documents: KnowledgeDocument[];
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  selectedNodeId: string | null;
  processingStatus: "idle" | "extracting" | "connecting" | "ready";
  focusArea: string | null;
}
