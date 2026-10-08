const E164 = /^\+[1-9][0-9]{7,14}$/;

export function normalizePhone(value: string): string {
  return value.replace(/[\s\-().]/g, "");
}

export function isValidPhone(normalized: string): boolean {
  return E164.test(normalized);
}
