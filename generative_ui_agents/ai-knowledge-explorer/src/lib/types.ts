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
