/**
 * ChatInput - Multi-line, auto-expanding input component.
 * Handles Enter/Shift+Enter, auto-focus, and responsive height.
 */

import { useState, useRef, useEffect, KeyboardEvent, FormEvent } from 'react';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export function ChatInput({ onSubmit, disabled, placeholder = 'Ask a question...' }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 200); // Max 200px
      textarea.style.height = `${newHeight}px`;
    }
  }, [value]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed && !disabled) {
      onSubmit(trimmed);
      setValue('');
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to submit, Shift+Enter for newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      formRef.current?.requestSubmit();
    }
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit} className="chat-input-form">
      <div className="chat-input-container">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="chat-input-textarea"
          maxLength={2000}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="chat-input-submit"
          aria-label="Send message"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    </form>
  );
}


