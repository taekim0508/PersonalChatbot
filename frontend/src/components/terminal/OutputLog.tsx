import { forwardRef, useEffect } from 'react';
import { OutputLine, LineType } from './OutputLine';

export interface LogEntry {
  id: string;
  content: string;
  type: LineType;
  isStreaming?: boolean;
}

interface OutputLogProps {
  entries: LogEntry[];
  typingLines?: string[];
  showTypingCursor?: boolean;
  onScrollToBottom?: () => void;
}

export const OutputLog = forwardRef<HTMLDivElement, OutputLogProps>(
  function OutputLog({ entries, typingLines = [], showTypingCursor = false, onScrollToBottom }, ref) {
    
    useEffect(() => {
      onScrollToBottom?.();
    }, [entries, typingLines, onScrollToBottom]);

    return (
      <div 
        ref={ref}
        className="flex-1 overflow-y-auto px-4 md:px-6 py-4 space-y-1 text-sm md:text-base"
        role="log"
        aria-live="polite"
        aria-label="Terminal output"
      >
        {/* Typewriter intro lines */}
        {typingLines.map((line, index) => (
          <OutputLine 
            key={`intro-${index}`}
            content={line}
            type="output"
            showCursor={showTypingCursor && index === typingLines.length - 1}
          />
        ))}

        {/* Conversation entries */}
        {entries.map((entry) => (
          <OutputLine
            key={entry.id}
            content={entry.content}
            type={entry.type}
            isStreaming={entry.isStreaming}
          />
        ))}
      </div>
    );
  }
);
