import { memo } from 'react';
import { LoadingIndicator } from './LoadingIndicator';

export type LineType = 'command' | 'output' | 'system' | 'typing';

interface OutputLineProps {
  content: string;
  type: LineType;
  showCursor?: boolean;
  isStreaming?: boolean;
}

export const OutputLine = memo(function OutputLine({ 
  content, 
  type, 
  showCursor = false,
  isStreaming = false,
}: OutputLineProps) {
  const getLineStyles = () => {
    switch (type) {
      case 'command':
        return 'text-foreground';
      case 'output':
        return 'text-foreground/90';
      case 'system':
        return 'terminal-dim';
      case 'typing':
        return 'terminal-dim italic';
      default:
        return 'text-foreground';
    }
  };

  // Check if content contains code block markers
  const renderContent = () => {
    if (content.includes('```')) {
      const parts = content.split(/(```[\s\S]*?```)/);
      return parts.map((part, i) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const code = part.slice(3, -3).replace(/^\w+\n/, '');
          return (
            <pre 
              key={i} 
              className="bg-[hsl(var(--terminal-surface))] px-3 py-2 my-2 rounded overflow-x-auto text-sm"
            >
              <code>{code}</code>
            </pre>
          );
        }
        return <span key={i}>{part}</span>;
      });
    }
    return content;
  };

  // Show loading indicator for typing entries with empty content
  if (type === 'typing' && !content.trim()) {
    return (
      <div className={getLineStyles()}>
        <LoadingIndicator />
      </div>
    );
  }

  return (
    <div className={`leading-relaxed whitespace-pre-wrap break-words ${getLineStyles()}`}>
      {type === 'command' && (
        <span className="terminal-prompt mr-2">{'>'}</span>
      )}
      {renderContent()}
      {showCursor && (
        <span className="inline-block w-2 h-4 ml-0.5 bg-[hsl(var(--terminal-cursor))] cursor-blink align-middle" />
      )}
      {isStreaming && !showCursor && (
        <span className="terminal-dim ml-1">▋</span>
      )}
    </div>
  );
});
