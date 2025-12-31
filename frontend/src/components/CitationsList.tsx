/**
 * CitationsList component - displays citations from the answer.
 * Expandable/collapsible list showing which chunks were cited.
 */

import { useState } from 'react';
import type { Citation } from '../types/api';

interface CitationsListProps {
  citations: Citation[];
}

export function CitationsList({ citations }: CitationsListProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (citations.length === 0) {
    return null;
  }

  return (
    <div className="citations-list">
      <button
        className="citations-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="citations-title">
          Citations ({citations.length})
        </span>
        <span className="citations-arrow">{isExpanded ? '▼' : '▶'}</span>
      </button>
      {isExpanded && (
        <div className="citations-content">
          {citations.map((citation, idx) => (
            <div key={idx} className="citation-item">
              <div className="citation-meta">
                <span className="citation-section">{citation.section}</span>
                {citation.entity && (
                  <span className="citation-entity"> • {citation.entity}</span>
                )}
              </div>
              <div className="citation-id">ID: {citation.chunk_id}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

