/**
 * LoadingState component - displays loading indicator.
 */

export function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-spinner"></div>
      <p className="loading-text">Searching resume and generating answer...</p>
    </div>
  );
}

