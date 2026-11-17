// Thin fetch wrapper: JSON in/out, bearer token, readable errors.

const TOKEN_KEY = "hm.token";

export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string | null) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage blocked: session-only login */
    }
  },
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

function errorMessage(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0] as { loc?: unknown[]; msg?: string };
      const field = first.loc?.[first.loc.length - 1];
      const msg = (first.msg ?? "Invalid value").replace(/^Value error, /, "");
      return field && typeof field === "string" ? `${field.replace(/_/g, " ")}: ${msg}` : msg;
    }
  }
  if (status >= 500) return "Server error. Please try again in a moment.";
  return `Request failed (${status})`;
}

type Query = Record<string, string | number | boolean | string[] | null | undefined>;

export function qs(params: Query): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "" || v === false) continue;
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, x));
    else sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export async function api<T>(
  path: string,
  init: { method?: string; body?: unknown; form?: FormData; headers?: Record<string, string> } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json", ...init.headers };
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  let body: BodyInit | undefined;
  if (init.form) body = init.form;
  else if (init.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(init.body);
  }

  let res: Response;
  try {
    res = await fetch(path, { method: init.method ?? "GET", headers, body });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check that the backend is running.");
  }

  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized?.();
    throw new ApiError(res.status, errorMessage(data, res.status));
  }
  return data as T;
}
