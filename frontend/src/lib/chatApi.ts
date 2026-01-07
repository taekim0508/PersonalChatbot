/**
 * Chat API integration with the FastAPI backend.
 * Provides streaming-like UX by chunking the response for display.
 * 
 * Purpose: This module wraps the API client to provide a streaming interface
 * for the terminal UI, even though the backend returns complete responses.
 * 
 * Why this design:
 * - TerminalPanel expects an async generator for streaming display
 * - Backend returns complete answers (not streaming)
 * - We simulate streaming by chunking words for better UX
 * - Keeps streaming logic separate from API client (single responsibility)
 */

import { sendChatRequest } from '@/api/client';
import type { ChatRequest } from '@/types/api';

/**
 * Sends a message to the backend and yields chunks for streaming display.
 * 
 * Purpose: Provides a streaming-like interface for the terminal UI.
 * The backend returns a complete response, but we chunk it word-by-word
 * to create a typewriter effect that feels more interactive.
 * 
 * @param message - The user's query message
 * @yields Chunks of the response text (words grouped together)
 * @throws Error if the API request fails
 * 
 * Why this implementation:
 * - Async generator allows TerminalPanel to consume chunks as they arrive
 * - Small delay between chunks creates natural typing effect
 * - Groups words into buffers (30+ chars) to avoid too many updates
 * - Handles errors gracefully with user-friendly messages
 * 
 * Design decisions:
 * 1. Simulated streaming rather than real streaming:
 *    - Backend doesn't support streaming yet
 *    - Simulated streaming still provides good UX
 *    - Can be upgraded to real streaming later without changing TerminalPanel
 * 
 * 2. Word-based chunking:
 *    - More natural than character-by-character
 *    - Faster than character streaming (less updates)
 *    - Still feels responsive and interactive
 * 
 * 3. Variable timing:
 *    - Random delay (20-50ms) makes typing feel more human
 *    - Prevents mechanical, predictable appearance
 */
export async function* sendMessage(message: string): AsyncGenerator<string> {
  try {
    // Small initial delay to show loading state immediately
    // This gives visual feedback that the request was received
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Construct the request matching backend schema
    // top_k: 6 is a good default (balance of context vs speed/cost)
    const request: ChatRequest = {
      query: message,
      top_k: 6,
    };

    // Send request to backend and wait for complete response
    // The API client handles HTTP communication and error handling
    const response = await sendChatRequest(request);

    // Simulate streaming by chunking the answer into word groups
    // This creates a typewriter effect even though we have the full response
    const words = response.answer.split(' ');
    let buffer = '';
    
    // Process words one at a time, grouping them into chunks
    for (let i = 0; i < words.length; i++) {
      // Add word to buffer (with space separator except for first word)
      buffer += (i === 0 ? '' : ' ') + words[i];
      
      // Yield chunk when buffer reaches threshold or we're at the last word
      // Threshold (30 chars) balances between too many updates and smooth appearance
      if (buffer.length > 30 || i === words.length - 1) {
        // Variable delay makes typing feel more natural
        // Random component (0-30ms) prevents mechanical appearance
        await new Promise((resolve) => setTimeout(resolve, 20 + Math.random() * 30));
        
        // Yield the chunk to the consumer (TerminalPanel)
        yield buffer;
        
        // Reset buffer for next chunk
        buffer = '';
      }
    }
  } catch (error) {
    // Handle errors gracefully with user-friendly messages
    // Extract error message if available, otherwise use generic message
    const errorMessage = error && typeof error === 'object' && 'message' in error
      ? (error as { message: string }).message
      : 'Unable to process your request. Please try again.';
    
    // Re-throw as Error so TerminalPanel can catch and display it
    throw new Error(errorMessage);
  }
}
