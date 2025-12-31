import { Sparkles } from "lucide-react";

export const TypingIndicator = () => {
  return (
    <div className="flex gap-3 px-4 md:px-6 animate-message-in">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-accent flex items-center justify-center flex-shrink-0 mt-1">
        <Sparkles className="w-4 h-4 text-primary" />
      </div>
      <div className="chat-bubble-bot px-4 py-3 rounded-2xl rounded-tl-md border border-border/50">
        <div className="flex gap-1.5 items-center">
          <span className="w-2 h-2 bg-primary/60 rounded-full typing-dot" />
          <span className="w-2 h-2 bg-primary/60 rounded-full typing-dot" />
          <span className="w-2 h-2 bg-primary/60 rounded-full typing-dot" />
          <span className="text-xs text-muted-foreground ml-2">Thinking...</span>
        </div>
      </div>
    </div>
  );
};


