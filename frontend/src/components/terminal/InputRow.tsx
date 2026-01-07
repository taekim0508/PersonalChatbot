import { useState, useRef, useEffect, KeyboardEvent, FormEvent } from 'react';

interface InputRowProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputRow({ onSubmit, disabled = false, placeholder = "Type a command..." }: InputRowProps) {
  const [value, setValue] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Re-focus when enabled
  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;

    // Add to history
    setHistory((prev) => [...prev.slice(-50), trimmed]);
    setHistoryIndex(-1);
    
    onSubmit(trimmed);
    setValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length === 0) return;
      
      const newIndex = historyIndex === -1 
        ? history.length - 1 
        : Math.max(0, historyIndex - 1);
      
      setHistoryIndex(newIndex);
      setValue(history[newIndex]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex === -1) return;
      
      const newIndex = historyIndex + 1;
      if (newIndex >= history.length) {
        setHistoryIndex(-1);
        setValue('');
      } else {
        setHistoryIndex(newIndex);
        setValue(history[newIndex]);
      }
    }
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="flex items-center gap-2 px-4 md:px-6 py-3 border-t border-[hsl(var(--terminal-border))] bg-[hsl(var(--terminal-bg))]"
    >
      <span className="terminal-prompt font-bold shrink-0" aria-hidden="true">
        {'>'}
      </span>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? "Processing..." : placeholder}
        className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:terminal-dim text-sm md:text-base caret-[hsl(var(--terminal-cursor))]"
        aria-label="Terminal input"
        autoComplete="off"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
      />
      {value && !disabled && (
        <span className="text-xs terminal-dim hidden sm:block">
          Press Enter ↵
        </span>
      )}
    </form>
  );
}
