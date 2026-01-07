/**
 * API client for communicating with the FastAPI backend.
 * 
 * Purpose: Centralized HTTP client that handles all backend API calls.
 * This keeps API logic in one place, making it easier to:
 * - Update API endpoints in one location
 * - Add authentication/headers consistently
 * - Handle errors uniformly
 * - Mock API calls for testing
 * 
 * Why this design:
 * - Single responsibility: only handles HTTP communication
 * - Uses fetch API (native, no dependencies)
 * - Leverages Vite proxy (configured in vite.config.ts) to avoid CORS issues
 * - Type-safe with TypeScript interfaces
 */

import type { ChatRequest, ChatResponse, ApiError } from '@/types/api';

/**
 * Base URL for API requests.
 * 
 * Purpose: Centralized API endpoint configuration.
 * 
 * Why this approach:
 * - In development: Uses relative path '/chat' which Vite proxies to backend
 *   (see vite.config.ts proxy configuration)
 * - In production: Would use full URL (can be set via env variable)
 * - Empty string means relative URLs, which work with the Vite proxy
 * 
 * Design decision: Using relative paths allows Vite's dev server proxy
 * to handle CORS and routing automatically, simplifying development.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Default headers for all API requests.
 * 
 * Purpose: Ensures consistent request format and content type.
 * 
 * Why these headers:
 * - 'Content-Type': application/json - Required for FastAPI to parse JSON body
 * - 'Accept': application/json - Tells backend we expect JSON response
 * 
 * Design decision: Setting headers here rather than per-request ensures
 * consistency and reduces code duplication.
 */
const DEFAULT_HEADERS: HeadersInit = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

/**
 * Sends a chat request to the backend and returns the response.
 * 
 * Purpose: Main function for sending user queries to the LLM backend.
 * 
 * @param request - Chat request containing query and top_k parameter
 * @returns Promise resolving to ChatResponse with answer and metadata
 * @throws Error if request fails (network error, API error, etc.)
 * 
 * Why this implementation:
 * - Uses async/await for clean error handling
 * - Validates response status before parsing JSON
 * - Provides detailed error messages for debugging
 * - Type-safe: returns ChatResponse matching backend schema
 * 
 * Design decisions:
 * 1. Throws errors rather than returning error objects - simpler error handling
 *    in calling code (can use try/catch)
 * 2. Checks response.ok - catches HTTP errors (4xx, 5xx) before parsing
 * 3. Extracts error message from response if available - better UX than generic errors
 * 4. Uses fetch API - native, no dependencies, modern async API
 */
export async function sendChatRequest(request: ChatRequest): Promise<ChatResponse> {
  try {
    // Construct the full URL
    // In dev: '/chat' gets proxied to 'http://localhost:8000/chat' by Vite
    // In prod: Would use full URL from API_BASE_URL
    const url = `${API_BASE_URL}/chat`;
    
    // Make the HTTP POST request
    // POST is required because we're sending a request body (the query)
    const response = await fetch(url, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify(request), // Convert request object to JSON string
    });

    // Check if request was successful (status 200-299)
    // If not, we need to handle the error before trying to parse JSON
    if (!response.ok) {
      // Try to extract error message from response body
      // Backend may return error details in JSON format
      let errorMessage = `API request failed with status ${response.status}`;
      
      try {
        const errorData = await response.json() as ApiError;
        errorMessage = errorData.message || errorData.detail || errorMessage;
      } catch {
        // If response isn't JSON, use status text as fallback
        errorMessage = response.statusText || errorMessage;
      }
      
      throw new Error(errorMessage);
    }

    // Parse JSON response into TypeScript object
    // TypeScript will validate structure matches ChatResponse interface
    const data = await response.json() as ChatResponse;
    
    return data;
  } catch (error) {
    // Handle network errors, JSON parsing errors, etc.
    // Re-throw with context for better error messages
    if (error instanceof Error) {
      // If it's already an Error (from our throw above), re-throw as-is
      throw error;
    }
    
    // For unexpected error types, wrap in Error
    throw new Error(
      error && typeof error === 'object' && 'message' in error
        ? String(error.message)
        : 'An unexpected error occurred while communicating with the server'
    );
  }
}

/**
 * Health check endpoint to verify backend is running.
 * 
 * Purpose: Allows frontend to check if backend is available before making requests.
 * 
 * @returns Promise resolving to health status
 * 
 * Why this exists:
 * - Useful for showing connection status in UI
 * - Can be called on app startup to verify backend is ready
 * - Helps with debugging connection issues
 * 
 * Design decision: Separate function keeps health checks simple and
 * doesn't require the full ChatRequest/ChatResponse types.
 */
export async function checkHealth(): Promise<{ status: string }> {
  const url = `${API_BASE_URL}/health`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: DEFAULT_HEADERS,
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return await response.json() as { status: string };
}

