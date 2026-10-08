"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";

import { configureApiClient } from "@/lib/apiClient";
import { toast } from "@/stores/toasts";

import { useAuthStore } from "./store";

// Wire the API client to the auth store once (handlers read the store lazily).
configureApiClient({
  getToken: () => useAuthStore.getState().token,
  onUnauthorized: () => {
    const { status, clearSession } = useAuthStore.getState();
    if (status !== "authenticated") return; // bootstrap / logout handle their own 401s
    clearSession();
    toast.info("You were signed out", "Please sign in again.");
  },
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

  // StrictMode-safe: bootstrap() shares one in-flight promise.
  useEffect(() => {
    void useAuthStore.getState().bootstrap();
  }, []);

  // Never leak one account's cached data into the next login.
  useEffect(
    () =>
      useAuthStore.subscribe((state, previous) => {
        if (previous.status === "authenticated" && state.status === "unauthenticated") {
          queryClient.clear();
        }
      }),
    [queryClient],
  );

  return <>{children}</>;
}
