"use client";

import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/cn";

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  label?: string;
  hint?: string;
  error?: string | null;
  leftIcon?: ReactNode;
  inputSize?: "sm" | "md" | "lg";
  /** Filled, borderless look used by search fields. */
  filled?: boolean;
}

const SIZES = { sm: "h-9 text-sm", md: "h-11", lg: "h-14 text-2xl" } as const;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, leftIcon, inputSize = "md", filled = false, className, id, ...rest },
  ref,
) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  return (
    <div className="flex w-full flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-fg text-sm font-medium">
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <span className="text-fg-subtle pointer-events-none absolute inset-y-0 left-3 flex items-center">
            {leftIcon}
          </span>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cn(
            "text-fg placeholder:text-fg-subtle w-full border px-3 transition-colors outline-none",
            "focus:border-brand focus:ring-brand/30 focus:ring-2",
            "disabled:cursor-not-allowed disabled:opacity-60",
            SIZES[inputSize],
            filled ? "bg-hover rounded-full border-transparent" : "bg-surface rounded-lg",
            !filled && (error ? "border-critical" : "border-line"),
            leftIcon && "pl-10",
            className,
          )}
          {...rest}
        />
      </div>
      {error ? (
        <p id={`${inputId}-error`} className="text-critical text-sm">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="text-fg-muted text-sm">
          {hint}
        </p>
      ) : null}
    </div>
  );
});
