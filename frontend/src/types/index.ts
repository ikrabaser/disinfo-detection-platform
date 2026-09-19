export type Role = "admin" | "analyst" | "viewer";

export interface PropagationNode {
  id: string;
  type?: string;
  attrs?: Record<string, unknown>;
}

export interface PropagationEdge {
  source: string;
  target: string;
  attrs?: Record<string, unknown>;
}

export interface PropagationGraphData {
  nodes: PropagationNode[];
  edges: PropagationEdge[];
}
