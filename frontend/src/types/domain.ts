export interface User {
  id: string;
  phone_number: string;
  username: string | null;
  display_name: string;
  about: string | null;
  avatar_url: string | null;
  avatar_color: string;
  last_seen_at: number | null;
  created_at: number;
}

export interface AuthResponse {
  token: string;
  token_type: "bearer";
  expires_at: number;
  user: User;
  is_new_user: boolean;
}

export interface OtpRequestResponse {
  sent: boolean;
  expires_in_s: number;
}
