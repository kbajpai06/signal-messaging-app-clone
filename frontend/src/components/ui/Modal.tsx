"use client";

import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";

import { cn } from "@/lib/cn";

import { IconButton } from "./IconButton";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md";
}

/** Built on the native <dialog>: focus trap, Esc, and top-layer stacking come for free. */
export function Modal({ open, onClose, title, children, footer, size = "md" }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    else if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={title ? titleId : undefined}
      // Fires on Esc and on programmatic close(); only notify the parent for the former.
      onClose={() => {
        if (open) onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose(); // backdrop click
      }}
      className={cn(
        "bg-surface text-fg m-auto w-[calc(100%-2rem)] rounded-[var(--radius-modal)] p-0 shadow-2xl",
        "backdrop:bg-black/50",
        size === "sm" ? "max-w-sm" : "max-w-md",
      )}
    >
      {open && (
        <div className="flex max-h-[85dvh] flex-col">
          {title && (
            <header className="flex items-center justify-between px-5 pt-4 pb-2">
              <h2 id={titleId} className="text-base font-semibold">
                {title}
              </h2>
              <IconButton label="Close" size="sm" onClick={onClose}>
                <X size={18} />
              </IconButton>
            </header>
          )}
          <div className="overflow-y-auto px-5 py-3">{children}</div>
          {footer && <footer className="flex justify-end gap-2 px-5 pt-2 pb-4">{footer}</footer>}
        </div>
      )}
    </dialog>
  );
}
