/**
 * TypingIndicator - Shows "assistant is typing" animation.
 * ChatGPT-style loading indicator.
 */

export function TypingIndicator() {
  return (
    <div className="message-bubble message-assistant">
      <div className="message-content-wrapper">
        <div className="typing-indicator">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}


