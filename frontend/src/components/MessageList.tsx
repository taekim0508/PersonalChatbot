/**
 * MessageList - Renders all chat messages with auto-scroll.
 * Handles smooth scrolling to newest message.
 */

import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import type { ChatMessage } from '../types/chat';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or loading state changes
  useEffect(() => {
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    };

    // Small delay to ensure DOM has updated
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
  }, [messages, isLoading]);

  // Also scroll on initial load
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
    }
  }, []);

  return (
    <div ref={containerRef} className="message-list">
      {messages.length === 0 && !isLoading && (
        <div className="message-list-empty">
          <p className="empty-title">Start a conversation</p>
          <p className="empty-subtitle">Ask me anything about my background, experience, or skills.</p>
          <div className="empty-examples">
            <p className="examples-title">Example questions:</p>
            <ul className="examples-list">
              <li>What is your experience with AI and LLMs?</li>
              <li>Tell me about your backend development experience</li>
              <li>What projects have you worked on?</li>
            </ul>
          </div>
        </div>
      )}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isLoading && <TypingIndicator />}
      <div ref={messagesEndRef} className="message-list-end" />
    </div>
  );
}


