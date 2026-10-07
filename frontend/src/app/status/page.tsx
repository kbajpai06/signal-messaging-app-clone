import { env } from "@/lib/env";
import { Suspense } from "react";
import { connection } from "next/server";

async function fetchBackendStatus(): Promise<string> {
  try {
    const res = await fetch(new URL("/health", env.apiUrl), { cache: "no-store" });
    if (!res.ok) return `unhealthy (HTTP ${res.status})`;
    const body = (await res.json()) as { status: string };
    return body.status;
  } catch {
    return "unreachable";
  }
}

async function BackendStatus() {
  await connection();
  const status = await fetchBackendStatus();
  const healthy = status === "ok";

  return (
    <p className="text-fg-muted">
      Backend status:{" "}
      <span className={healthy ? "font-medium text-green-600" : "font-medium text-red-600"}>
        {status}
      </span>
    </p>
  );
}

export default function StatusPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-3">
      <h1 className="text-2xl font-semibold">Signal Clone</h1>
      <Suspense fallback={<p className="text-fg-muted">Backend status: checking...</p>}>
        <BackendStatus />
      </Suspense>
    </main>
  );
}
