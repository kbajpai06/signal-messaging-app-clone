import { AuthGate, LoginForm } from "@/features/auth";

export default function LoginPage() {
  return (
    <AuthGate mode="guest">
      <LoginForm />
    </AuthGate>
  );
}
