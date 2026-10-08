import { create } from "zustand";

import type { ToastData } from "@/components/ui/Toast";

const MAX_VISIBLE = 3;
const DEFAULT_DURATION_MS = 4000;
let nextId = 0;

interface ToastState {
  toasts: ToastData[];
  push: (toast: Omit<ToastData, "id">, durationMs?: number) => string;
  dismiss: (id: string) => void;
}

export const useToastStore = create<ToastState>()((set, get) => ({
  toasts: [],
  push: (toast, durationMs = DEFAULT_DURATION_MS) => {
    const id = String(++nextId);
    set((state) => ({ toasts: [...state.toasts.slice(-(MAX_VISIBLE - 1)), { ...toast, id }] }));
    if (durationMs > 0 && typeof window !== "undefined") {
      window.setTimeout(() => get().dismiss(id), durationMs);
    }
    return id;
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

/** Imperative helpers, usable from anywhere (event handlers, api hooks, WS router). */
export const toast = {
  success: (title: string, description?: string) =>
    useToastStore.getState().push({ kind: "success", title, description }),
  error: (title: string, description?: string) =>
    useToastStore.getState().push({ kind: "error", title, description }, 6000),
  info: (title: string, description?: string) =>
    useToastStore.getState().push({ kind: "info", title, description }),
};
