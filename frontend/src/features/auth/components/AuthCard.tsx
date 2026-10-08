import type { ReactNode } from "react";

import { SignalLogo } from "@/components/ui/SignalLogo";

interface AuthCardProps {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
}

export function AuthCard({ title, subtitle, children }: AuthCardProps) {
  return (
    <div className="w-full max-w-sm">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <SignalLogo className="text-brand size-16" />
        <h1 className="text-2xl font-semibold">{title}</h1>
        {subtitle && <p className="text-fg-muted">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}
