/**
 * API client for communicating with the FastAPI backend.
 * Handles HTTP requests, error handling, and type safety.
 */

import type { ChatRequest, ChatResponse, ApiError } from '../types/api';

// Use environment variable if set, otherwise use relative URL for dev proxy or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.DEV ? '' : 'http://localhost:8000');

/**
 * Sends a chat query to the backend and returns the response.
 * 
 * @param request - The chat request with query and optional top_k
 * @returns Promise resolving to ChatResponse
 * @throws ApiError if the request fails
 */
export async function sendChatRequest(request: ChatRequest): Promise<ChatResponse> {
  const url = `${API_BASE_URL}/chat`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: request.query,
        top_k: request.top_k ?? 6,
      }),
    });

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      let errorDetails: string | undefined;
      
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
        errorDetails = JSON.stringify(errorData);
      } catch {
        // If response isn't JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }

      const error: ApiError = {
        message: errorMessage,
        status: response.status,
        details: errorDetails,
      };
      throw error;
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    // Handle network errors or other exceptions
    if (error instanceof TypeError && error.message.includes('fetch')) {
      const apiError: ApiError = {
        message: 'Network error: Could not connect to backend. Make sure the server is running.',
        details: error.message,
      };
      throw apiError;
    }
    
    // Re-throw ApiError instances
    if (error && typeof error === 'object' && 'message' in error) {
      throw error;
    }
    
    // Wrap unexpected errors
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      details: error instanceof Error ? error.message : String(error),
    };
    throw apiError;
  }
}

