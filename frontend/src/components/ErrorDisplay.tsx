/**
 * ErrorDisplay component - displays error messages gracefully.
 */

import type { ApiError } from '../types/api';

interface ErrorDisplayProps {
  error: ApiError;
  onDismiss?: () => void;
}

export function ErrorDisplay({ error, onDismiss }: ErrorDisplayProps) {
  const isNetworkError = error.message.includes('Network error');
  const isServerError = error.status && error.status >= 500;
  const isClientError = error.status && error.status >= 400 && error.status < 500;

  let errorTitle = 'Error';
  if (isNetworkError) {
    errorTitle = 'Connection Error';
  } else if (isServerError) {
    errorTitle = 'Server Error';
  } else if (isClientError) {
    errorTitle = 'Request Error';
  }

  return (
    <div className="error-display" role="alert">
      <div className="error-header">
        <h3 className="error-title">{errorTitle}</h3>
        {onDismiss && (
          <button
            className="error-dismiss"
            onClick={onDismiss}
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
      <p className="error-message">{error.message}</p>
      {error.details && (
        <details className="error-details">
          <summary>Technical details</summary>
          <pre className="error-details-content">{error.details}</pre>
        </details>
      )}
      {isNetworkError && (
        <div className="error-help">
          <p>Please ensure:</p>
          <ul>
            <li>The backend server is running</li>
            <li>The API URL is correct (check VITE_API_BASE_URL)</li>
            <li>There are no CORS issues</li>
          </ul>
        </div>
      )}
    </div>
  );
}

