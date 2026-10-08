"use client";

import { Phone } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { getErrorMessage } from "@/lib/errors";
import { isValidPhone, normalizePhone } from "@/lib/phone";

import { requestOtp } from "../api";
import { DEMO_ACCOUNTS } from "../demoAccounts";
import { useAuthStore } from "../store";
import { AuthCard } from "./AuthCard";

export function LoginForm() {
  const router = useRouter();
  const setPendingPhone = useAuthStore((s) => s.setPendingPhone);
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const phone = normalizePhone(value);
    if (!isValidPhone(phone)) {
      setError("Enter your number with the country code, e.g. +1 555 000 0001");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await requestOtp(phone);
      setPendingPhone(phone);
      router.push("/verify");
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't send the code. Please try again."));
      setSubmitting(false);
    }
  }

  return (
    <AuthCard title="Your phone number" subtitle="Enter your phone number to get started.">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <Input
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          autoFocus
          aria-label="Phone number"
          placeholder="+1 555 000 0001"
          leftIcon={<Phone size={16} />}
          value={value}
          onChange={(event) => {
            setValue(event.target.value);
            setError(null);
          }}
          error={error}
        />
        <Button type="submit" size="lg" fullWidth loading={submitting}>
          Next
        </Button>
      </form>

      <div className="mt-8">
        <p className="text-fg-subtle mb-2 text-xs font-medium tracking-wide uppercase">
          Demo accounts
        </p>
        <div className="flex flex-wrap gap-2">
          {DEMO_ACCOUNTS.map((account) => (
            <button
              key={account.phone}
              type="button"
              onClick={() => {
                setValue(account.phone);
                setError(null);
              }}
              className="bg-hover hover:bg-line rounded-full px-3 py-1 text-sm transition-colors"
            >
              {account.name}
            </button>
          ))}
        </div>
      </div>
    </AuthCard>
  );
}
