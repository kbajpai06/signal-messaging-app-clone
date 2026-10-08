import { env } from "@/lib/env";

const ABSOLUTE = /^(https?:|blob:|data:)/i;

/** Backend stores avatars as "/uploads/..." paths. Resolve against the API origin. */
export function resolveAssetUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined;
  if (ABSOLUTE.test(path)) return path;
  return new URL(path, env.apiUrl).href;
}
