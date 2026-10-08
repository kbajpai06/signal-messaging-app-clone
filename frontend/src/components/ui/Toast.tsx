"use client";

import { CircleAlert, CircleCheck, Info, X } from "lucide-react";

import { cn } from "@/lib/cn";

export interface ToastData {
  id: string;
  kind: "success" | "error" | "info";
  title: string;
  description?: string;
}

const ICONS = { success: CircleCheck, error: CircleAlert, info: Info } as const;

interface ToastViewportProps {
  toasts: ToastData[];
  onDismiss: (id: string) => void;
}

/** Presentational: the host component feeds it from the toast store. */
export function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-6 z-100 flex flex-col items-center gap-2 px-4"
    >
      {toasts.map((toast) => {
        const Icon = ICONS[toast.kind];
        return (
          <div
            key={toast.id}
            role="status"
            className="bg-fg text-surface pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl px-4 py-3 shadow-lg"
          >
            <Icon
              size={18}
              className={cn(
                "mt-0.5 shrink-0",
                toast.kind === "success" && "text-green-400",
                toast.kind === "error" && "text-red-400",
              )}
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">{toast.title}</p>
              {toast.description && <p className="text-sm opacity-80">{toast.description}</p>}
            </div>
            <button
              type="button"
              aria-label="Dismiss"
              onClick={() => onDismiss(toast.id)}
              className="shrink-0 opacity-70 hover:opacity-100"
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
