import { cn } from "@/lib/cn";

/** Simple speech-bubble mark. Colored via `currentColor`. */
export function SignalLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true" className={cn("size-12", className)}>
      <path
        fill="currentColor"
        d="M24 4C12.95 4 4 12.4 4 22.8c0 4.3 1.6 8.3 4.3 11.4L6 43l8.6-3.6A21.4 21.4 0 0 0 24 41.6c11.05 0 20-8.4 20-18.8S35.05 4 24 4Z"
      />
      <circle
        cx="24"
        cy="22.8"
        r="12"
        fill="none"
        stroke="white"
        strokeWidth="2"
        strokeDasharray="2 3.2"
        strokeLinecap="round"
      />
    </svg>
  );
}
