import { ApiError } from "@/lib/apiClient";

const DEFAULT_MESSAGE = "Something went wrong. Please try again.";

export function getErrorMessage(err: unknown, fallback: string = DEFAULT_MESSAGE): string {
  if (err instanceof ApiError) {
    const first = err.details[0];
    if (err.code === "validation_error" && first) {
      return first.message.charAt(0).toUpperCase() + first.message.slice(1);
    }
    return err.message || fallback;
  }
  return fallback;
}
