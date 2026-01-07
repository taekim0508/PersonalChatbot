import { useState, useCallback, useEffect, useRef } from 'react';
import { TerminalHeader } from './TerminalHeader';
import { OutputLog, LogEntry } from './OutputLog';
import { InputRow } from './InputRow';
import { useTypewriter } from '@/hooks/useTypewriter';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { sendMessage } from '@/lib/chatApi';

const INTRO_LINES = [
  'tae@portfolio:~$ boot --portfolio-chat',
  'Initializing Tae Portfolio Chatbot...',
  'Ready. Ask questions about Tae\'s background and projects.',
  '',
  'Try:',
  '  - "What\'s Tae\'s backend experience?"',
  '  - "What projects has Tae built with FastAPI?"',
  '  - "Explain Tae\'s RAG chatbot architecture."',
  '  - "What experience does Tae have with real-time systems?"',
  '  - "Summarize Tae\'s strengths for a new grad SWE role."',
  '',
  'Commands:',
  '  help   → show examples',
  '  clear  → clear screen',
  '  about  → short bio',
  '',
  'Type a question and press Enter.',
];

const HELP_LINES = [
  '',
  'Available commands and example questions:',
  '',
  '  help   → show this message',
  '  clear  → clear the terminal',
  '  about  → display a short bio',
  '',
  'Example questions:',
  '  - "What\'s Tae\'s backend experience?"',
  '  - "What projects has Tae built with FastAPI?"',
  '  - "Explain Tae\'s RAG chatbot architecture."',
  '  - "What experience with real-time systems?"',
  '',
];

const ABOUT_LINES = [
  '',
  '┌────────────────────────────────────────────┐',
  '│  Tae - Software Engineer                   │',
  '├────────────────────────────────────────────┤',
  '│  🎓 CS Graduate | Full-Stack Developer     │',
  '│  💻 Python, TypeScript, React, FastAPI     │',
  '│  🚀 Passionate about clean code & UX       │',
  '│  📍 Open to new grad SWE opportunities     │',
  '└────────────────────────────────────────────┘',
  '',
];

export function TerminalPanel() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [introComplete, setIntroComplete] = useState(false);
  const entryIdRef = useRef(0);

  const { containerRef, scrollToBottom } = useAutoScroll<HTMLDivElement>();

  const { displayedLines, isTyping, skip } = useTypewriter({
    lines: INTRO_LINES,
    typingSpeed: 25,
    lineDelay: 100,
    startDelay: 300,
    onComplete: () => setIntroComplete(true),
  });

  const generateId = () => {
    entryIdRef.current += 1;
    return `entry-${entryIdRef.current}`;
  };

  const addEntry = useCallback((content: string, type: LogEntry['type'], isStreaming = false) => {
    const id = generateId();
    setEntries((prev) => [...prev, { id, content, type, isStreaming }]);
    return id;
  }, []);

  const updateEntry = useCallback((id: string, content: string, isStreaming = false) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.id === id ? { ...entry, content, isStreaming } : entry
      )
    );
  }, []);

  // Scroll effect
  useEffect(() => {
    scrollToBottom();
  }, [entries, displayedLines, scrollToBottom]);

  // Handle skip intro on keypress
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isTyping && (e.key === 'Escape' || e.key === 'Enter')) {
        skip();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isTyping, skip]);

  const handleCommand = async (input: string) => {
    const command = input.toLowerCase().trim();

    // Echo user input
    addEntry(input, 'command');

    // Handle built-in commands
    if (command === 'clear') {
      setEntries([]);
      addEntry('Terminal cleared.', 'system');
      return;
    }

    if (command === 'help') {
      HELP_LINES.forEach((line) => addEntry(line, 'output'));
      return;
    }

    if (command === 'about') {
      ABOUT_LINES.forEach((line) => addEntry(line, 'output'));
      return;
    }

    // Send to AI
    setIsProcessing(true);
    const responseId = addEntry('...', 'typing', true);

    try {
      let fullResponse = '';
      
      // Stream the response
      for await (const chunk of sendMessage(input)) {
        fullResponse += chunk;
        updateEntry(responseId, fullResponse, true);
        scrollToBottom();
      }

      // Mark as complete
      updateEntry(responseId, fullResponse, false);
    } catch (error) {
      console.error('Chat error:', error);
      updateEntry(responseId, 'Error: Unable to process your request. Please try again.', false);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8 bg-background">
      <div 
        className="w-full max-w-4xl h-[85vh] md:h-[80vh] flex flex-col bg-[hsl(var(--terminal-bg))] rounded-lg terminal-glow relative overflow-hidden scanlines crt-curve crt-flicker crt-refresh phosphor-glow"
        role="application"
        aria-label="Tae Portfolio Chatbot Terminal"
      >
        <TerminalHeader />
        
        <OutputLog
          ref={containerRef}
          entries={entries}
          typingLines={displayedLines}
          showTypingCursor={isTyping}
          onScrollToBottom={scrollToBottom}
        />

        <InputRow
          onSubmit={handleCommand}
          disabled={!introComplete || isProcessing}
          placeholder={isTyping ? "Press Enter or Esc to skip intro..." : "Ask about Tae's experience..."}
        />

        {/* Skip hint during intro */}
        {isTyping && (
          <div className="absolute bottom-16 right-4 text-xs terminal-dim animate-pulse">
            Press Enter to skip
          </div>
        )}
      </div>
    </div>
  );
}
