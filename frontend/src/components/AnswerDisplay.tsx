/**
 * AnswerDisplay component - displays the LLM-generated answer in chat format.
 */

interface AnswerDisplayProps {
  answer: string;
  query: string;
}

export function AnswerDisplay({ answer, query }: AnswerDisplayProps) {
  // Split answer by newlines to preserve formatting
  const paragraphs = answer.split("\n").filter((p) => p.trim());

  return (
    <div className="chat-messages">
      {/* User Query Bubble */}
      <div className="chat-message user-message">
        <div className="message-content">{query}</div>
      </div>

      {/* AI Answer Bubble */}
      <div className="chat-message ai-message">
        <div className="message-content">
          {paragraphs.length > 0 ? (
            paragraphs.map((paragraph, idx) => (
              <p key={idx} className="answer-paragraph">
                {paragraph}
              </p>
            ))
          ) : (
            <p className="answer-paragraph">{answer}</p>
          )}
        </div>
      </div>
    </div>
  );
}
