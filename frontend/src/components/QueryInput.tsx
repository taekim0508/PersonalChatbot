/**
 * QueryInput component - handles user input for chat queries.
 */

import { useState, FormEvent } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function QueryInput({ onSubmit, isLoading, disabled }: QueryInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmedQuery = query.trim();
    if (trimmedQuery && !isLoading && !disabled) {
      onSubmit(trimmedQuery);
      setQuery(''); // Clear input after submission
    }
  };

  return (
    <form onSubmit={handleSubmit} className="query-input-form">
      <div className="query-input-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about my background..."
          disabled={isLoading || disabled}
          className="query-input"
          maxLength={2000}
          autoFocus
        />
        <button
          type="submit"
          disabled={isLoading || disabled || !query.trim()}
          className="query-submit-button"
        >
          {isLoading ? 'Searching...' : 'Ask'}
        </button>
      </div>
    </form>
  );
}
