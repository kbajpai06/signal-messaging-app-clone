"use client";

import { User as UserIcon } from "lucide-react";
import { useState } from "react";

import { resolveAssetUrl } from "@/lib/assets";
import { cn } from "@/lib/cn";

interface AvatarProps {
  name: string;
  src?: string | null;
  /** Fallback background (the backend's deterministic avatar_color). */
  color?: string;
  size?: number;
  online?: boolean;
  className?: string;
}

function getInitials(name: string): string {
  if (!/\p{L}/u.test(name)) return ""; // phone numbers etc. get the generic icon
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "";
  const first = parts[0].charAt(0);
  const last = parts.length > 1 ? parts[parts.length - 1].charAt(0) : "";
  return (first + last).toUpperCase();
}

export function Avatar({ name, src, color, size = 48, online, className }: AvatarProps) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const url = resolveAssetUrl(src);
  const showImage = Boolean(url) && failedSrc !== url;
  const initials = getInitials(name);
  const dot = Math.max(8, Math.round(size * 0.25));

  return (
    <span
      className={cn("relative inline-flex shrink-0", className)}
      style={{ width: size, height: size }}
    >
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url}
          alt=""
          draggable={false}
          onError={() => setFailedSrc(url ?? null)}
          className="size-full rounded-full object-cover"
        />
      ) : (
        <span
          aria-hidden="true"
          className="flex size-full items-center justify-center rounded-full font-semibold text-white select-none"
          style={{
            backgroundColor: color ?? "var(--color-primary)",
            fontSize: Math.round(size * 0.38),
          }}
        >
          {initials || <UserIcon size={Math.round(size * 0.5)} />}
        </span>
      )}
      {online && (
        <span
          aria-label="Online"
          style={{ width: dot, height: dot }}
          className="bg-presence ring-surface absolute right-0 bottom-0 rounded-full ring-2"
        />
      )}
    </span>
  );
}
