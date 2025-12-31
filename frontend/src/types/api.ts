/**
 * TypeScript interfaces matching the FastAPI backend schema.
 * These types ensure type safety between frontend and backend.
 */

export interface Citation {
  chunk_id: string;
  section: string;
  entity: string;
}

export interface RetrievedEvidence {
  id: string;
  score: number;
  section: string;
  entity: string;
  keywords: string[];
  text_preview: string;
}

export interface ChatRequest {
  query: string;
  top_k?: number; // Optional, defaults to 6 on backend
}

export interface ChatResponse {
  query: string;
  top_k: number;
  answer: string;
  citations: Citation[];
  evidence: RetrievedEvidence[];
}

export interface ApiError {
  message: string;
  status?: number;
  details?: string;
}

