import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { AuthGate } from "@/features/auth";
import { ConversationSidebar } from "@/features/conversations";

export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGate mode="app">
      <AppShell sidebar={<ConversationSidebar />}>{children}</AppShell>
    </AuthGate>
  );
}
