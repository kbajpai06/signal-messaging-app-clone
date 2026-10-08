import { api } from "@/lib/apiClient";
import type { AuthResponse, OtpRequestResponse, User } from "@/types/domain";

export const requestOtp = (phoneNumber: string) =>
  api.post<OtpRequestResponse>("/auth/otp/request", { phone_number: phoneNumber }, { auth: false });

export const verifyOtp = (phoneNumber: string, code: string) =>
  api.post<AuthResponse>("/auth/otp/verify", { phone_number: phoneNumber, code }, { auth: false });

export const fetchMe = () => api.get<User>("/auth/me");

export const logout = () =>
  api.post<void>("/auth/logout", undefined, { handleUnauthorized: false });

export interface ProfileChanges {
  display_name?: string;
  about?: string | null;
  username?: string | null;
}

export const updateProfile = (changes: ProfileChanges) => api.put<User>("/users/me", changes);

export function uploadAvatar(file: File): Promise<User> {
  const form = new FormData();
  form.append("file", file);
  return api.upload<User>("/users/me/avatar", form);
}
