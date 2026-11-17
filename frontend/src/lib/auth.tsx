import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setUnauthorizedHandler, tokenStore } from "./api";
import type { Role, TokenOut, User } from "./types";

interface SignupInput {
  name: string;
  email: string;
  phone?: string;
  password: string;
  role: "buyer" | "seller";
}

interface AuthState {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (input: SignupInput) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  const logout = useCallback(() => {
    tokenStore.set(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    if (!tokenStore.get()) {
      setReady(true);
      return;
    }
    api<User>("/api/auth/me")
      .then(setUser)
      .catch(() => tokenStore.set(null))
      .finally(() => setReady(true));
  }, [logout]);

  const accept = useCallback((t: TokenOut) => {
    tokenStore.set(t.access_token);
    setUser(t.user);
    return t.user;
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      ready,
      logout,
      login: (email, password) =>
        api<TokenOut>("/api/auth/login", { method: "POST", body: { email, password } }).then(accept),
      signup: (input) => api<TokenOut>("/api/auth/signup", { method: "POST", body: input }).then(accept),
    }),
    [user, ready, logout, accept],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}

/** Where each role lands after signing in. */
export function homeFor(role: Role): string {
  switch (role) {
    case "admin":
      return "/console";
    case "sales_agent":
      return "/console/leads";
    case "seller":
      return "/console/listings";
    default:
      return "/listings";
  }
}
