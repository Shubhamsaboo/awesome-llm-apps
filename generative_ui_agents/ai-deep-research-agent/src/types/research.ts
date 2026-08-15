/**
 * Research State Types
 *
 * Types for managing research state in the Deep Research Assistant.
 * Uses local state + useDefaultTool pattern instead of useCoAgent
 * to avoid type mismatches with Python FilesystemMiddleware.
 */

export interface Todo {
  id: string;
  content: string;
  status: "pending" | "in_progress" | "completed";
}

export interface ResearchFile {
  path: string;
  content: string;
  createdAt: string;
}

// Sources found via internet_search (includes content)
export interface Source {
  url: string;
  title: string;
  content?: string;
  status: "found" | "scraped" | "failed";
}

export interface ResearchState {
  todos: Todo[];
  files: ResearchFile[];
  sources: Source[];
}

export const INITIAL_STATE: ResearchState = {
  todos: [],
  files: [],
  sources: [],
};
