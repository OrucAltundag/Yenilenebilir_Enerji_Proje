"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";

import { api, clearSession, getStoredSession, type AuthSession } from "@/lib/api";

export function AuthPanel() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [username, setUsername] = useState("analyst");
  const [password, setPassword] = useState("analyst123");

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

  const login = useMutation({
    mutationFn: () => api.login(username, password),
    onSuccess: setSession,
  });

  if (session) {
    return (
      <section className="panel auth-panel" aria-label="Oturum bilgisi">
        <div>
          <div className="eyebrow">Oturum</div>
          <strong>{session.username}</strong>{" "}
          <span className="muted">({session.role})</span>
        </div>
        <nav className="top-links" aria-label="Uygulama menüsü">
          <Link href="/projects">Projeler</Link>
          {session.role === "admin" && <Link href="/admin">Admin</Link>}
          <button
            className="ghost-button"
            type="button"
            onClick={() => {
              clearSession();
              setSession(null);
            }}
          >
            Çıkış
          </button>
        </nav>
      </section>
    );
  }

  return (
    <section className="panel auth-panel" aria-label="Demo oturum açma">
      <div>
        <div className="eyebrow">Demo oturum</div>
        <p className="muted compact">
          Kullanıcı testleri için analyst/analyst123 veya admin/admin123.
        </p>
      </div>
      <form
        className="login-form"
        onSubmit={(event) => {
          event.preventDefault();
          login.mutate();
        }}
      >
        <input
          aria-label="Kullanıcı adı"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
        <input
          aria-label="Parola"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <button type="submit" disabled={login.isPending}>
          {login.isPending ? "Giriş…" : "Giriş yap"}
        </button>
      </form>
      {login.error && <p className="error-text">{(login.error as Error).message}</p>}
    </section>
  );
}
