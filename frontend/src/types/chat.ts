/**
 * Chat-specific types for message management and UI state.
 */

import type { Citation, RetrievedEvidence } from './api';

export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  isLoading?: boolean;
  error?: string;
  metadata?: {
    citations?: Citation[];
    evidence?: RetrievedEvidence[];
  };
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}


