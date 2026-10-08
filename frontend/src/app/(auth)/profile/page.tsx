import { AuthGate, ProfileForm } from "@/features/auth";

export default function ProfilePage() {
  return (
    <AuthGate mode="onboarding">
      <ProfileForm />
    </AuthGate>
  );
}
