import { cn } from "@/lib/utils";

export const Cursor = ({ className }: { className?: string }) => {
  return (
    <div
      className={cn(
        "w-3 h-3 ml-3 rounded-full bg-accent/10 border border-accent/40 animate-pulse",
        className,
      )}
    />
  );
};
