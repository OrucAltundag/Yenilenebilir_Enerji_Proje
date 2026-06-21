"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import { api, clearSession, getStoredSession, type AuthSession } from "@/lib/api";

// QA UI-1: demo kullanıcı/parola ipucunu yalnız NEXT_PUBLIC_SHOW_DEMO_HINT=1
// olduğunda göster; üretim build'inde varsayılan olarak gizli.
const SHOW_DEMO_HINT =
  process.env.NEXT_PUBLIC_SHOW_DEMO_HINT === "1" ||
  process.env.NEXT_PUBLIC_SHOW_DEMO_HINT === "true";

export function AuthPanel() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [username, setUsername] = useState(SHOW_DEMO_HINT ? "analyst" : "");
  const [password, setPassword] = useState(SHOW_DEMO_HINT ? "analyst123" : "");
  const pathname = usePathname();
  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname?.startsWith(href));

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
          <Link href="/" className={isActive("/") && pathname === "/" ? "active" : undefined}>
            Ana sayfa
          </Link>
          <Link href="/projects" className={isActive("/projects") ? "active" : undefined}>
            Projeler
          </Link>
          <Link href="/compare" className={isActive("/compare") ? "active" : undefined}>Karşılaştır</Link>
          <Link href="/reports" className={isActive("/reports") ? "active" : undefined}>Raporlar</Link>
          <Link href="/methodology" className={isActive("/methodology") ? "active" : undefined}>Metodoloji</Link>
          {(session.role === "developer" || session.role === "admin") && (
            <Link href="/developer" className={isActive("/developer") ? "active" : undefined}>
              Yazılımcı
            </Link>
          )}
          {session.role === "admin" && (
            <Link href="/admin" className={isActive("/admin") ? "active" : undefined}>
              Admin
            </Link>
          )}
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
    <section className="panel auth-panel" aria-label="Oturum açma">
      <div>
        <div className="eyebrow">Oturum aç</div>
        {SHOW_DEMO_HINT ? (
          <p className="muted compact">
            Demo: analyst/analyst123, developer/developer123 veya admin/admin123.
          </p>
        ) : (
          <p className="muted compact">
            Kullanıcı adı ve parolanızla giriş yapın.
          </p>
        )}
      </div>
      <form
        className="login-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (!username.trim() || !password) return;
          login.mutate();
        }}
      >
        <input
          aria-label="Kullanıcı adı"
          autoComplete="username"
          name="username"
          required
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
        <input
          aria-label="Parola"
          autoComplete="current-password"
          name="password"
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <button
          type="submit"
          disabled={login.isPending || !username.trim() || !password}
        >
          {login.isPending ? "Giriş…" : "Giriş yap"}
        </button>
      </form>
      {login.error && (
        <p className="error-text" role="alert" aria-live="assertive">
          {(login.error as Error).message}
        </p>
      )}
    </section>
  );
}
