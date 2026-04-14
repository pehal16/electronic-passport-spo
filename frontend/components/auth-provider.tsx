"use client";

import { ReactNode, createContext, useContext, useEffect, useState } from "react";

import { LoginResponse, User } from "@/lib/types";

interface AuthContextValue {
  token: string | null;
  user: User | null;
  isReady: boolean;
  signIn: (payload: LoginResponse) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const TOKEN_KEY = "spo-passport-token";
const USER_KEY = "spo-passport-user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const savedToken = window.localStorage.getItem(TOKEN_KEY);
    const savedUser = window.localStorage.getItem(USER_KEY);
    if (savedToken) {
      setToken(savedToken);
    }
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser) as User);
      } catch {
        window.localStorage.removeItem(USER_KEY);
      }
    }
    setIsReady(true);
  }, []);

  const value: AuthContextValue = {
    token,
    user,
    isReady,
    signIn: (payload) => {
      window.localStorage.setItem(TOKEN_KEY, payload.access_token);
      window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
      setToken(payload.access_token);
      setUser(payload.user);
    },
    signOut: () => {
      window.localStorage.removeItem(TOKEN_KEY);
      window.localStorage.removeItem(USER_KEY);
      setToken(null);
      setUser(null);
      window.location.href = "/login";
    }
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth должен использоваться внутри AuthProvider.");
  }
  return context;
}
