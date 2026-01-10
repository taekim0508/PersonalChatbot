import { useMemo } from "react";
import { Cpu } from "lucide-react";

const loadingMessages = [
  "Thinking...",
  "Compiling data...",
  "Processing query...",
  "Analyzing context...",
  "Retrieving information...",
  "Synthesizing response...",
  "Running inference...",
  "Parsing knowledge base...",
  "Generating answer...",
  "Optimizing response...",
];

export const LoadingIndicator = () => {
  // Pick a random message when component mounts (each new request gets a different message)
  const currentMessage = useMemo(() => {
    return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
  }, []);

  return (
    <div className="flex items-center gap-3 terminal-dim">
      <div className="relative flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping opacity-75" />
        <Cpu className="w-4 h-4 text-primary relative z-10 animate-spin-slow" />
      </div>
      <span className="text-sm italic">{currentMessage}</span>
      <span className="flex gap-1">
        <span className="w-1.5 h-1.5 bg-primary/60 rounded-full typing-dot" />
        <span className="w-1.5 h-1.5 bg-primary/60 rounded-full typing-dot" />
        <span className="w-1.5 h-1.5 bg-primary/60 rounded-full typing-dot" />
      </span>
    </div>
  );
};
