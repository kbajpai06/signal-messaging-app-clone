import { AuthGate, VerifyForm } from "@/features/auth";

export default function VerifyPage() {
  return (
    <AuthGate mode="guest">
      <VerifyForm />
    </AuthGate>
  );
}
