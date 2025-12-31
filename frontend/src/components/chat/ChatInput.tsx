import { useState, KeyboardEvent, useRef, useEffect } from "react";
import { Send, Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [message]);

  return (
    <div className="chat-input-area px-4 md:px-6 py-4 sticky bottom-0 border-t border-border/50">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-3 bg-muted/50 rounded-2xl p-2 border border-border/50">
          <button className="p-2 rounded-xl hover:bg-background transition-colors flex-shrink-0 mb-0.5">
            <Paperclip className="w-5 h-5 text-muted-foreground" />
          </button>

          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            disabled={disabled}
            rows={1}
            className={cn(
              "flex-1 resize-none bg-transparent py-2",
              "text-[15px] placeholder:text-muted-foreground",
              "focus:outline-none",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            style={{ minHeight: "24px", maxHeight: "150px" }}
          />

          <button
            onClick={handleSend}
            disabled={!message.trim() || disabled}
            className={cn(
              "p-2.5 rounded-xl transition-all flex-shrink-0 mb-0.5",
              message.trim() && !disabled
                ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
                : "bg-muted text-muted-foreground"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-[11px] text-muted-foreground text-center mt-2">
          Press Enter to send, Shift + Enter for new line
        </p>
      </div>
    </div>
  );
};


