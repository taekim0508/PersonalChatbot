interface TerminalHeaderProps {
  title?: string;
}

export function TerminalHeader({ title = "tae@portfolio" }: TerminalHeaderProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-[hsl(var(--terminal-header))] border-b border-[hsl(var(--terminal-border))] rounded-t-lg">
      {/* macOS-style window dots */}
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-[hsl(var(--terminal-dot-red))] opacity-80" />
        <div className="w-3 h-3 rounded-full bg-[hsl(var(--terminal-dot-yellow))] opacity-80" />
        <div className="w-3 h-3 rounded-full bg-[hsl(var(--terminal-dot-green))] opacity-80" />
      </div>
      
      {/* Title */}
      <span className="text-sm terminal-dim flex-1 text-center pr-12">
        {title}
      </span>
    </div>
  );
}
