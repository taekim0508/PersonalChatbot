import { useState, useEffect } from "react";
import { Brain, Sparkles, Cpu, Zap } from "lucide-react";

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

const icons = [Brain, Sparkles, Cpu, Zap];

export const LoadingIndicator = () => {
  const [currentMessage, setCurrentMessage] = useState(0);
  const [currentIcon, setCurrentIcon] = useState(0);

  // Rotate messages every 2 seconds
  useEffect(() => {
    const messageInterval = setInterval(() => {
      setCurrentMessage((prev) => (prev + 1) % loadingMessages.length);
    }, 2000);

    // Rotate icons every 1.5 seconds
    const iconInterval = setInterval(() => {
      setCurrentIcon((prev) => (prev + 1) % icons.length);
    }, 1500);

    return () => {
      clearInterval(messageInterval);
      clearInterval(iconInterval);
    };
  }, []);

  const IconComponent = icons[currentIcon];

  return (
    <div className="flex items-center gap-3 terminal-dim">
      <div className="relative flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping opacity-75" />
        <IconComponent 
          className="w-4 h-4 text-primary relative z-10 animate-spin-slow" 
        />
      </div>
      <span className="text-sm italic transition-opacity duration-500">
        {loadingMessages[currentMessage]}
      </span>
      <span className="flex gap-1">
        <span className="w-1.5 h-1.5 bg-primary/60 rounded-full typing-dot" />
        <span className="w-1.5 h-1.5 bg-primary/60 rounded-full typing-dot" />
        <span className="w-1.5 h-1.5 bg-primary/60 rounded-full typing-dot" />
      </span>
    </div>
  );
};

