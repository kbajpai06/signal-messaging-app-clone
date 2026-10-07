function required(name: string, value: string | undefined): string {
  if (!value) throw new Error(`Missing environment variable: ${name}`);
  return value;
}

export const env = {
  apiUrl: required("NEXT_PUBLIC_API_URL", process.env.NEXT_PUBLIC_API_URL),
  wsUrl: required("NEXT_PUBLIC_WS_URL", process.env.NEXT_PUBLIC_WS_URL),
} as const;
