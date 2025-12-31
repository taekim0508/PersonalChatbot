/**
 * MessageBubble - Individual chat message component.
 * Handles user and assistant message rendering with proper formatting.
 */

import type { ChatMessage } from '../types/chat';
import { CitationsList } from './CitationsList';
import { EvidenceList } from './EvidenceList';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {

  // Format content with line breaks and basic markdown-like formatting
  const formatContent = (content: string): React.ReactNode[] => {
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      // Handle bullet points (lines starting with - or *)
      if (/^[-*]\s/.test(line)) {
        return (
          <div key={idx} className="message-bullet-point">
            {line}
          </div>
        );
      }
      // Handle numbered lists (lines starting with number.)
      if (/^\d+\.\s/.test(line)) {
        return (
          <div key={idx} className="message-numbered-point">
            {line}
          </div>
        );
      }
      // Regular paragraph
      if (line.trim()) {
        return (
          <p key={idx} className="message-paragraph">
            {line}
          </p>
        );
      }
      // Empty line for spacing
      return <br key={idx} />;
    });
  };

  const isUser = message.role === 'user';
  const hasMetadata = message.metadata && (
    message.metadata.citations?.length || message.metadata.evidence?.length
  );

  return (
    <div className={`message-bubble ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-content-wrapper">
        <div className="message-content">
          {message.error ? (
            <div className="message-error">
              <strong>Error:</strong> {message.error}
            </div>
          ) : (
            formatContent(message.content)
          )}
        </div>
        {!isUser && hasMetadata && (
          <div className="message-metadata">
            {message.metadata?.citations && message.metadata.citations.length > 0 && (
              <CitationsList citations={message.metadata.citations} />
            )}
            {message.metadata?.evidence && message.metadata.evidence.length > 0 && (
              <EvidenceList evidence={message.metadata.evidence} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

