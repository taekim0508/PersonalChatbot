/**
 * ChatContainer - Main chat interface orchestrator.
 * Manages message state, API calls, and coordinates child components.
 */

import { useState, useCallback } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { sendChatRequest } from '../api/client';
import type { ChatMessage } from '../types/chat';
import type { ApiError } from '../types/api';

export function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateMessageId = () => `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  const handleSendMessage = useCallback(async (content: string) => {
    // Immediately add user message
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Create placeholder for assistant response
    const assistantMessageId = generateMessageId();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await sendChatRequest({ query: content, top_k: 6 });

      // Update assistant message with response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: response.answer,
                isLoading: false,
                metadata: {
                  citations: response.citations,
                  evidence: response.evidence,
                },
              }
            : msg
        )
      );
    } catch (err) {
      // Update assistant message with error
      const errorMessage =
        err && typeof err === 'object' && 'message' in err
          ? (err as ApiError).message
          : 'An unexpected error occurred';

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: '',
                isLoading: false,
                error: errorMessage,
              }
            : msg
        )
      );
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="chat-container">
      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSubmit={handleSendMessage} disabled={isLoading} />
    </div>
  );
}


