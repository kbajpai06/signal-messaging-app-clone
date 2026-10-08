import { env } from "@/lib/env";

export interface ApiErrorDetail {
  field: string;
  message: string;
}

interface ApiErrorBody {
  error?: { code?: string; message?: string; details?: ApiErrorDetail[] };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];

  constructor(status: number, code: string, message: string, details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** status 0 = the request never reached the server. */
  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

interface Hooks {
  getToken: () => string | null;
  onUnauthorized: () => void;
}

let hooks: Hooks = { getToken: () => null, onUnauthorized: () => {} };

/** The auth feature plugs itself in here, so this module never imports a feature. */
export function configureApiClient(next: Partial<Hooks>): void {
  hooks = { ...hooks, ...next };
}

type QueryValue = string | number | boolean | null | undefined;

export interface RequestOptions {
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
  /** Attach the bearer token. Default true. */
  auth?: boolean;
  /** Fire the global 401 handler. Default true. */
  handleUnauthorized?: boolean;
}

interface InternalOptions extends RequestOptions {
  json?: unknown;
  form?: FormData;
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const base = env.apiUrl.replace(/\/+$/, "");
  const url = new URL(`${base}${path.startsWith("/") ? path : `/${path}`}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function toApiError(status: number, data: unknown): ApiError {
  const err = (data as ApiErrorBody | null)?.error;
  return new ApiError(
    status,
    err?.code ?? "http_error",
    err?.message ?? `Request failed (${status})`,
    err?.details ?? [],
  );
}

async function request<T>(method: string, path: string, options: InternalOptions = {}): Promise<T> {
  const headers = new Headers({ Accept: "application/json" });
  let body: BodyInit | undefined;

  if (options.form) {
    body = options.form; // the browser sets the multipart boundary
  } else if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }

  if (options.auth !== false) {
    const token = hooks.getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), {
      method,
      headers,
      body,
      signal: options.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, "network_error", "Can't reach the server. Check your connection.");
  }

  if (response.status === 204) return undefined as T;

  const data = await parseJson(response);
  if (!response.ok) {
    const error = toApiError(response.status, data);
    if (response.status === 401 && options.auth !== false && options.handleUnauthorized !== false) {
      hooks.onUnauthorized();
    }
    throw error;
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, { ...options, json }),
  put: <T>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>("PUT", path, { ...options, json }),
  patch: <T>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>("PATCH", path, { ...options, json }),
  delete: <T = void>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
  upload: <T>(path: string, form: FormData, options?: RequestOptions) =>
    request<T>("POST", path, { ...options, form }),
};
