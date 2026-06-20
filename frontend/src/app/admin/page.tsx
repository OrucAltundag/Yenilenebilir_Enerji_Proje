"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { AuthPanel } from "@/components/AuthPanel";
import { api, getStoredSession, type AuthSession } from "@/lib/api";

export default function AdminPage() {
  const [version, setVersion] = useState("2023.1");
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

  const isAdmin = session?.role === "admin";

  const active = useQuery({
    queryKey: ["admin-active"],
    queryFn: api.activeDataset,
    retry: false,
    enabled: isAdmin,
  });
  const audit = useQuery({
    queryKey: ["admin-audit"],
    queryFn: () => api.auditLog(20),
    retry: false,
    enabled: isAdmin,
  });
  const publish = useMutation({
    mutationFn: () => api.publishDataset(version),
    onSuccess: () => {
      active.refetch();
      audit.refetch();
    },
  });
  const rollback = useMutation({
    mutationFn: () => api.rollbackDataset(version),
    onSuccess: () => {
      active.refetch();
      audit.refetch();
    },
  });

  return (
    <main className="page-shell">
      <Link href="/" className="back-link">
        ← Ana sayfa
      </Link>
      <header className="hero-header">
        <div>
          <h1>Admin paneli</h1>
          <p className="muted">
            Veri sürümü yayınlama, geri alma ve audit kayıtlarını kullanıcı testinde
            doğrulamak için.
          </p>
        </div>
      </header>
      <AuthPanel />

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Aktif veri sürümü</h2>
          {!isAdmin ? (
            <p className="error-text">
              Admin yetkisi gerekiyor. admin/admin123 ile giriş yapın.
            </p>
          ) : active.error ? (
            <p className="error-text">{(active.error as Error).message}</p>
          ) : (
            <p className="big-stat">{active.data?.active ?? "—"}</p>
          )}
          <label className="field-stack">
            <span>Sürüm</span>
            <input value={version} onChange={(event) => setVersion(event.target.value)} />
          </label>
          <div className="button-row">
            <button
              type="button"
              onClick={() => publish.mutate()}
              disabled={publish.isPending}
            >
              Yayınla
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => rollback.mutate()}
              disabled={rollback.isPending}
            >
              Geri al
            </button>
          </div>
          {(publish.error || rollback.error) && (
            <p className="error-text">
              {((publish.error || rollback.error) as Error).message}
            </p>
          )}
          {(publish.isSuccess || rollback.isSuccess) && (
            <p className="success-text">İşlem tamamlandı.</p>
          )}
        </div>

        <div className="panel">
          <h2>Audit log</h2>
          {!isAdmin ? (
            <p className="error-text">Audit için admin yetkisi gerekiyor.</p>
          ) : audit.error ? (
            <p className="error-text">{(audit.error as Error).message}</p>
          ) : (
            <div className="card-list">
              {audit.data?.map((entry, index) => (
                <article key={`${entry.created_at}-${index}`} className="mini-card">
                  <strong>{entry.action}</strong>
                  <p className="muted compact">
                    {entry.actor} · {new Date(entry.created_at).toLocaleString("tr-TR")}
                  </p>
                  <pre className="mini-json">{JSON.stringify(entry.detail, null, 2)}</pre>
                </article>
              ))}
              {audit.data?.length === 0 && <p className="muted">Audit kaydı yok.</p>}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
