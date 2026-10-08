import { create } from "zustand";

import { ApiError } from "@/lib/apiClient";
import { tokenStorage } from "@/lib/tokenStorage";
import type { AuthResponse, User } from "@/types/domain";

import { fetchMe, logout } from "./api";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "error";

interface AuthState {
  status: AuthStatus;
  token: string | null;
  user: User | null;
  /** Phone number carried from /login to /verify. In memory only. */
  pendingPhone: string | null;

  setPendingPhone: (phone: string | null) => void;
  signIn: (result: Pick<AuthResponse, "token" | "user">) => void;
  setUser: (user: User) => void;
  /** Local-only: drops the token and user. Used on logout and on 401. */
  clearSession: () => void;
  signOut: () => Promise<void>;
  /** Restores the session from storage. Idempotent; `force` re-runs it (retry button). */
  bootstrap: (force?: boolean) => Promise<void>;
}

let settled = false;
let inFlight: Promise<void> | null = null;

export const useAuthStore = create<AuthState>()((set, get) => ({
  status: "loading",
  token: null,
  user: null,
  pendingPhone: null,

  setPendingPhone: (pendingPhone) => set({ pendingPhone }),

  signIn: ({ token, user }) => {
    tokenStorage.set(token);
    set({ token, user, status: "authenticated", pendingPhone: null });
  },

  setUser: (user) => set({ user }),

  clearSession: () => {
    tokenStorage.clear();
    set({ token: null, user: null, status: "unauthenticated", pendingPhone: null });
  },

  signOut: async () => {
    try {
      await logout(); // revokes the server session (and closes its sockets)
    } catch {
      /* the local session is dropped regardless */
    }
    get().clearSession();
  },

  bootstrap: (force = false) => {
    if (inFlight) return inFlight;
    if (settled && !force) return Promise.resolve();

    inFlight = (async () => {
      const token = tokenStorage.get();
      if (!token) {
        set({ token: null, status: "unauthenticated" });
        settled = true;
        return;
      }
      set({ token, status: "loading" });
      try {
        const user = await fetchMe();
        set({ user, status: "authenticated" });
        settled = true;
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          get().clearSession();
          settled = true;
        } else {
          // Server unreachable / cold start: keep the token and offer a retry.
          set({ status: "error" });
        }
      }
    })().finally(() => {
      inFlight = null;
    });

    return inFlight;
  },
}));
