const KEY = "signal.token";

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null; // blocked storage (private mode, etc.)
  }
}

export const tokenStorage = {
  get(): string | null {
    try {
      return storage()?.getItem(KEY) ?? null;
    } catch {
      return null;
    }
  },
  set(token: string): void {
    try {
      storage()?.setItem(KEY, token);
    } catch {
      /* ignore */
    }
  },
  clear(): void {
    try {
      storage()?.removeItem(KEY);
    } catch {
      /* ignore */
    }
  },
};
