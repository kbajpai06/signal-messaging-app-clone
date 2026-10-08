"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { getErrorMessage } from "@/lib/errors";
import { toast } from "@/stores/toasts";

import { requestOtp, verifyOtp } from "../api";
import { DEMO_OTP } from "../demoAccounts";
import { useAuthStore } from "../store";
import { AuthCard } from "./AuthCard";

const CODE_LENGTH = 6;

export function VerifyForm() {
  const router = useRouter();
  const phone = useAuthStore((s) => s.pendingPhone);
  const status = useAuthStore((s) => s.status);
  const signIn = useAuthStore((s) => s.signIn);

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const inFlight = useRef(false);

  // A refresh loses the in-memory phone number: start over. (Not while signed in:
  // signIn clears it and AuthGate is already redirecting.)
  useEffect(() => {
    if (!phone && status === "unauthenticated") router.replace("/login");
  }, [phone, status, router]);

  async function submit(value: string) {
    if (!phone || inFlight.current) return;
    inFlight.current = true;
    setSubmitting(true);
    setError(null);
    try {
      signIn(await verifyOtp(phone, value)); // AuthGate redirects: new user -> /profile
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't verify the code. Please try again."));
      setCode("");
      setSubmitting(false);
      inFlight.current = false;
      inputRef.current?.focus();
    }
  }

  async function resend() {
    if (!phone) return;
    setResending(true);
    try {
      await requestOtp(phone);
      toast.success("Code sent", "A new verification code is on its way.");
    } catch (err) {
      toast.error("Couldn't resend the code", getErrorMessage(err));
    } finally {
      setResending(false);
    }
  }

  if (!phone) return null;

  return (
    <AuthCard
      title="Enter your code"
      subtitle={
        <>
          Code sent to <span className="text-fg font-medium">{phone}</span>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Input
          ref={inputRef}
          autoFocus
          readOnly={submitting}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={CODE_LENGTH}
          aria-label="Verification code"
          placeholder="••••••"
          inputSize="lg"
          className="text-center tracking-[0.5em]"
          value={code}
          onChange={(event) => {
            const digits = event.target.value.replace(/\D/g, "").slice(0, CODE_LENGTH);
            setCode(digits);
            setError(null);
            if (digits.length === CODE_LENGTH) void submit(digits);
          }}
          error={error}
          hint={`Demo mode: the code is ${DEMO_OTP}`}
        />
        <Button
          size="lg"
          fullWidth
          loading={submitting}
          disabled={code.length !== CODE_LENGTH}
          onClick={() => void submit(code)}
        >
          Verify
        </Button>
        <div className="flex justify-between">
          <Button variant="ghost" size="sm" loading={resending} onClick={() => void resend()}>
            Resend code
          </Button>
          <Button variant="ghost" size="sm" onClick={() => router.replace("/login")}>
            Wrong number?
          </Button>
        </div>
      </div>
    </AuthCard>
  );
}
