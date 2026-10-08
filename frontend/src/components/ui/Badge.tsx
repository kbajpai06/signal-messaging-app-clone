import { cn } from "@/lib/cn";

interface BadgeProps {
  count: number;
  max?: number;
  tone?: "brand" | "muted";
  className?: string;
}

export function Badge({ count, max = 99, tone = "brand", className }: BadgeProps) {
  if (count <= 0) return null;
  return (
    <span
      title={`${count} unread`}
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-semibold text-white",
        tone === "brand" ? "bg-brand" : "bg-fg-subtle",
        className,
      )}
    >
      {count > max ? `${max}+` : count}
    </span>
  );
}
