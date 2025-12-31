import { Settings, Sparkles } from "lucide-react";

interface ChatHeaderProps {
  name: string;
  status?: string;
}

export const ChatHeader = ({ name, status = "Online" }: ChatHeaderProps) => {
  return (
    <header className="chat-header px-4 md:px-6 py-4 flex items-center gap-4 sticky top-0 z-10 border-b border-border/50">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center shadow-sm">
        <Sparkles className="w-5 h-5 text-primary-foreground" />
      </div>

      <div className="flex-1 min-w-0">
        <h1 className="font-semibold text-foreground text-lg tracking-tight">{name}</h1>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <p className="text-xs text-muted-foreground font-medium">{status}</p>
        </div>
      </div>

      <button className="p-2.5 rounded-xl hover:bg-muted transition-colors">
        <Settings className="w-5 h-5 text-muted-foreground" />
      </button>
    </header>
  );
};


