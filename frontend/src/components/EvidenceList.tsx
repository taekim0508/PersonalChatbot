/**
 * EvidenceList component - displays retrieved evidence chunks.
 * Expandable/collapsible list showing all retrieved chunks with scores.
 */

import { useState } from 'react';
import type { RetrievedEvidence } from '../types/api';

interface EvidenceListProps {
  evidence: RetrievedEvidence[];
}

export function EvidenceList({ evidence }: EvidenceListProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  if (evidence.length === 0) {
    return (
      <div className="evidence-list">
        <div className="evidence-empty">
          No evidence retrieved for this query.
        </div>
      </div>
    );
  }

  const toggleItem = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  // Sort by score descending
  const sortedEvidence = [...evidence].sort((a, b) => b.score - a.score);

  return (
    <div className="evidence-list">
      <button
        className="evidence-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="evidence-title">
          Retrieved Evidence ({evidence.length})
        </span>
        <span className="evidence-arrow">{isExpanded ? '▼' : '▶'}</span>
      </button>
      {isExpanded && (
        <div className="evidence-content">
          {sortedEvidence.map((item) => {
            const isItemExpanded = expandedItems.has(item.id);
            return (
              <div key={item.id} className="evidence-item">
                <button
                  className="evidence-item-header"
                  onClick={() => toggleItem(item.id)}
                >
                  <div className="evidence-item-meta">
                    <span className="evidence-score">
                      Score: {item.score.toFixed(3)}
                    </span>
                    <span className="evidence-section">{item.section}</span>
                    {item.entity && (
                      <span className="evidence-entity"> • {item.entity}</span>
                    )}
                  </div>
                  <span className="evidence-item-arrow">
                    {isItemExpanded ? '▼' : '▶'}
                  </span>
                </button>
                {isItemExpanded && (
                  <div className="evidence-item-content">
                    <div className="evidence-keywords">
                      <strong>Keywords:</strong>{' '}
                      {item.keywords.length > 0
                        ? item.keywords.join(', ')
                        : 'None'}
                    </div>
                    <div className="evidence-preview">
                      <strong>Preview:</strong>
                      <p>{item.text_preview}</p>
                    </div>
                    <div className="evidence-id">ID: {item.id}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

