"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

interface AppShellProps {
  sidebar: ReactNode;
  children: ReactNode;
}

/**
 * Split-pane layout: fixed-width list on the left, outlet on the right.
 * Below `md` it collapses to one pane: the list at "/", the chat at "/c/...".
 */
export function AppShell({ sidebar, children }: AppShellProps) {
  const pathname = usePathname();
  const inChat = pathname.startsWith("/c/");

  return (
    <div className="bg-surface flex h-dvh w-full overflow-hidden">
      <aside
        className={cn(
          "border-line bg-sidebar w-full shrink-0 flex-col border-r md:flex md:w-[var(--size-sidebar)]",
          inChat ? "hidden" : "flex",
        )}
      >
        {sidebar}
      </aside>
      <main className={cn("min-w-0 flex-1 flex-col md:flex", inChat ? "flex" : "hidden")}>
        {children}
      </main>
    </div>
  );
}
