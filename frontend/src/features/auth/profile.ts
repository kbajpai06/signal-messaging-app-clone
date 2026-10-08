import type { User } from "@/types/domain";

/**
 * The backend seeds new users with their phone number as display name (Phase 2),
 * so "still equals the phone number" means onboarding is not finished.
 */
export function isProfileComplete(user: User): boolean {
  return user.display_name.trim() !== "" && user.display_name !== user.phone_number;
}
