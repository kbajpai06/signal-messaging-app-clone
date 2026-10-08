"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

import { Tooltip } from "./Tooltip";

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "aria-label"> {
  /** Required: used as the accessible name and the tooltip. */
  label: string;
  size?: "sm" | "md" | "lg";
}

const SIZES = { sm: "size-8", md: "size-9", lg: "size-10" } as const;

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, size = "md", className, type = "button", children, ...rest },
  ref,
) {
  return (
    <Tooltip label={label}>
      <button
        ref={ref}
        type={type}
        aria-label={label}
        className={cn(
          "text-fg-muted inline-flex items-center justify-center rounded-full transition-colors",
          "hover:bg-hover hover:text-fg",
          "focus-visible:outline-brand focus-visible:outline-2 focus-visible:outline-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          SIZES[size],
          className,
        )}
        {...rest}
      >
        {children}
      </button>
    </Tooltip>
  );
});
