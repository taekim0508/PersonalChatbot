import { useState, useEffect, useCallback, useRef } from 'react';

interface TypewriterOptions {
  lines: string[];
  typingSpeed?: number;
  lineDelay?: number;
  startDelay?: number;
  onComplete?: () => void;
}

export function useTypewriter({
  lines,
  typingSpeed = 30,
  lineDelay = 150,
  startDelay = 500,
  onComplete,
}: TypewriterOptions) {
  const [displayedLines, setDisplayedLines] = useState<string[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const clearTimeouts = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Start typing after initial delay
  useEffect(() => {
    timeoutRef.current = setTimeout(() => {
      setIsTyping(true);
    }, startDelay);

    return clearTimeouts;
  }, [startDelay, clearTimeouts]);

  // Type characters
  useEffect(() => {
    if (!isTyping || isComplete) return;

    if (currentLineIndex >= lines.length) {
      setIsComplete(true);
      setIsTyping(false);
      onComplete?.();
      return;
    }

    const currentLine = lines[currentLineIndex];

    if (currentCharIndex < currentLine.length) {
      // Add jitter for realistic typing feel
      const jitter = Math.random() * 20 - 10;
      const delay = typingSpeed + jitter;

      timeoutRef.current = setTimeout(() => {
        setDisplayedLines((prev) => {
          const newLines = [...prev];
          if (newLines.length <= currentLineIndex) {
            newLines.push(currentLine.slice(0, currentCharIndex + 1));
          } else {
            newLines[currentLineIndex] = currentLine.slice(0, currentCharIndex + 1);
          }
          return newLines;
        });
        setCurrentCharIndex((prev) => prev + 1);
      }, delay);
    } else {
      // Move to next line
      timeoutRef.current = setTimeout(() => {
        setCurrentLineIndex((prev) => prev + 1);
        setCurrentCharIndex(0);
      }, lineDelay);
    }

    return clearTimeouts;
  }, [isTyping, isComplete, currentLineIndex, currentCharIndex, lines, typingSpeed, lineDelay, onComplete, clearTimeouts]);

  const skip = useCallback(() => {
    clearTimeouts();
    setDisplayedLines(lines);
    setIsComplete(true);
    setIsTyping(false);
    onComplete?.();
  }, [lines, onComplete, clearTimeouts]);

  return {
    displayedLines,
    isTyping,
    isComplete,
    currentLineIndex,
    skip,
  };
}
