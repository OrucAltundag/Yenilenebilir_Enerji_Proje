"use client";

import { useEffect, useState } from "react";

import { getStoredSession, type AuthSession } from "@/lib/api";

export function useAuthSession() {
  const [session, setSession] = useState<AuthSession | null>(null);

  useEffect(() => {
    const sync = () => setSession(getStoredSession());
    sync();
    window.addEventListener("buraki-auth-change", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("buraki-auth-change", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return session;
}
