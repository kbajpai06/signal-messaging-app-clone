"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface DropdownItem {
  key: string;
  label: string;
  icon?: ReactNode;
  destructive?: boolean;
  onSelect: () => void;
}

interface DropdownProps {
  items: DropdownItem[];
  header?: ReactNode;
  align?: "start" | "end";
  trigger: (state: { open: boolean; toggle: () => void }) => ReactNode;
}

export function Dropdown({ items, header, align = "start", trigger }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      {trigger({ open, toggle: () => setOpen((value) => !value) })}
      {open && (
        <div
          role="menu"
          className={cn(
            "border-line bg-surface absolute top-full z-40 mt-1 min-w-56 rounded-xl border p-1 shadow-lg",
            align === "end" ? "right-0" : "left-0",
          )}
        >
          {header && <div className="border-line border-b">{header}</div>}
          {items.map((item) => (
            <button
              key={item.key}
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                item.onSelect();
              }}
              className={cn(
                "hover:bg-hover flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm",
                item.destructive ? "text-critical" : "text-fg",
              )}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
