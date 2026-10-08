"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { SignalLogo } from "@/components/ui/SignalLogo";
import { Spinner } from "@/components/ui/Spinner";
import type { User } from "@/types/domain";

import { isProfileComplete } from "./profile";
import { useAuthStore, type AuthStatus } from "./store";

/**
 * guest:      /login, /verify    (signed-in users are sent onward)
 * onboarding: /profile           (signed in, profile not finished)
 * app:        everything else    (signed in with a finished profile)
 */
export type GateMode = "guest" | "onboarding" | "app";

export function resolveRedirect(
  mode: GateMode,
  status: AuthStatus,
  user: User | null,
): string | null {
  if (status !== "authenticated" || !user) return mode === "guest" ? null : "/login";
  const complete = isProfileComplete(user);
  if (mode === "guest") return complete ? "/" : "/profile";
  if (mode === "onboarding") return complete ? "/" : null;
  return complete ? null : "/profile";
}

function Splash({ children }: { children?: ReactNode }) {
  return (
    <div className="bg-surface flex min-h-dvh flex-col items-center justify-center gap-6 px-6 text-center">
      <SignalLogo className="text-brand size-16" />
      {children ?? <Spinner className="text-brand" />}
    </div>
  );
}

export function AuthGate({ mode, children }: { mode: GateMode; children: ReactNode }) {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);

  const settled = status === "authenticated" || status === "unauthenticated";
  const target = settled ? resolveRedirect(mode, status, user) : null;

  useEffect(() => {
    if (target) router.replace(target);
  }, [target, router]);

  if (status === "loading") return <Splash />;

  if (status === "error") {
    return (
      <Splash>
        <div className="flex max-w-xs flex-col items-center gap-3">
          <p className="text-fg-muted">
            Can&apos;t reach the server. If it was idle it may still be waking up, which can take up
            to a minute.
          </p>
          <Button onClick={() => void useAuthStore.getState().bootstrap(true)}>Try again</Button>
        </div>
      </Splash>
    );
  }

  if (target) return <Splash />;
  return <>{children}</>;
}
