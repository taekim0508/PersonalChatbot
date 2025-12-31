import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { User, Sparkles } from "lucide-react";

interface ChatBubbleProps {
  message: string;
  isUser: boolean;
  timestamp: string;
  showAvatar?: boolean;
}

export const ChatBubble = ({ message, isUser, timestamp, showAvatar = true }: ChatBubbleProps) => {
  return (
    <div
      className={cn(
        "flex gap-3 px-4 md:px-6 animate-message-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      {showAvatar ? (
        <div
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-gradient-to-br from-primary/20 to-accent text-primary"
          )}
        >
          {isUser ? (
            <User className="w-4 h-4" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
        </div>
      ) : (
        <div className="w-8 flex-shrink-0" />
      )}

      {/* Bubble */}
      <div className={cn("flex flex-col max-w-[85%] md:max-w-[75%]", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "px-4 py-3 rounded-2xl text-[15px] leading-relaxed",
            isUser
              ? "chat-bubble-user rounded-tr-md"
              : "chat-bubble-bot rounded-tl-md border border-border/50"
          )}
        >
          {isUser ? (
            <span>{message}</span>
          ) : (
            <MarkdownRenderer content={message} />
          )}
        </div>
        <span className="text-[11px] text-muted-foreground mt-1.5 px-1">
          {timestamp}
        </span>
      </div>
    </div>
  );
};


