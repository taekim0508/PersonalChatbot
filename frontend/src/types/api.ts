/**
 * TypeScript type definitions matching the FastAPI backend schema.
 * 
 * Purpose: These types ensure type safety between frontend and backend,
 * catching mismatches at compile time rather than runtime.
 * 
 * Why this structure:
 * - Matches the Pydantic models in backend/app/chat/schema.py exactly
 * - Enables TypeScript IntelliSense and type checking
 * - Makes refactoring safer by catching breaking changes early
 */

/**
 * Request payload sent to the /chat endpoint.
 * 
 * Purpose: Defines the structure of chat requests from frontend to backend.
 * 
 * Why these fields:
 * - query: The user's question (required, 1-2000 chars per backend validation)
 * - top_k: Number of chunks to retrieve (1-12, default 6)
 *   - Higher values = more context but slower/more expensive
 *   - 6 is a good balance for most queries
 */
export interface ChatRequest {
  query: string;
  top_k?: number; // Optional with default, but we'll usually provide it
}

/**
 * Evidence chunk retrieved from the knowledge base.
 * 
 * Purpose: Represents a relevant document chunk that was used to answer the query.
 * 
 * Why these fields:
 * - id: Unique identifier for the chunk (used for citations)
 * - score: Relevance score from retrieval (higher = more relevant)
 * - section: Which section of the resume/document this came from
 * - entity: What entity/person this relates to (useful for filtering)
 * - keywords: Tags associated with this chunk (used for relevance filtering)
 * - text_preview: First 500 chars of the chunk (for debugging/transparency)
 */
export interface RetrievedEvidence {
  id: string;
  score: number;
  section: string;
  entity: string;
  keywords: string[];
  text_preview: string;
}

/**
 * Citation reference to a specific chunk.
 * 
 * Purpose: Links parts of the LLM's answer back to source chunks.
 * 
 * Why this structure:
 * - chunk_id: Links to the specific chunk that was cited
 * - section: Human-readable section name (e.g., "Experience", "Projects")
 * - entity: Entity name if applicable (e.g., "FastAPI Project")
 * 
 * Design decision: Separate from RetrievedEvidence because citations
 * are what the LLM explicitly referenced, while evidence is all chunks
 * that were considered.
 */
export interface Citation {
  chunk_id: string;
  section: string;
  entity: string;
}

/**
 * Complete response from the /chat endpoint.
 * 
 * Purpose: Contains the LLM's answer plus metadata about sources.
 * 
 * Why these fields:
 * - query: Echo of the original query (useful for debugging/logging)
 * - top_k: Echo of the top_k parameter used
 * - answer: The LLM-generated response text (main content)
 * - citations: Chunks explicitly cited by the LLM in its answer
 * - evidence: All chunks that were retrieved and considered (broader than citations)
 * 
 * Design decision: Separating citations from evidence allows us to:
 * 1. Show what the LLM explicitly referenced (citations)
 * 2. Show all context that influenced the answer (evidence)
 * 3. Provide transparency about the retrieval process
 */
export interface ChatResponse {
  query: string;
  top_k: number;
  answer: string;
  citations: Citation[];
  evidence: RetrievedEvidence[];
}

/**
 * Error response structure for API errors.
 * 
 * Purpose: Standardized error format for consistent error handling.
 * 
 * Why this structure:
 * - message: Human-readable error message to display to users
 * - detail: Optional technical details for debugging
 * 
 * Design decision: Matches FastAPI's default error response format,
 * making error handling predictable across the application.
 */
export interface ApiError {
  message: string;
  detail?: string;
}

