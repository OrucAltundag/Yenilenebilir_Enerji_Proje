"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { AuthPanel } from "@/components/AuthPanel";
import { useAuthSession } from "@/hooks/useAuthSession";

const links = [
  ["/developer", "Genel bakış"],
  ["/developer/training", "Eğitimler"],
  ["/developer/models", "Modeller"],
  ["/developer/compare", "Karşılaştırma"],
  ["/developer/data-quality", "Veri kalitesi"],
  ["/developer/health", "Sistem sağlığı"],
  ["/developer/logs", "Loglar"],
  ["/developer/approvals", "Onaylar"],
] as const;

export function DeveloperShell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  const session = useAuthSession();
  const allowed = session?.role === "developer" || session?.role === "admin";

  return (
    <main className="page-shell">
      <Link href="/" className="back-link">← Ana sayfa</Link>
      <header className="hero-header"><div><h1>{title}</h1><p className="muted">{description}</p></div></header>
      <AuthPanel />
      {allowed && <nav className="developer-nav" aria-label="Yazılımcı paneli menüsü">{links.map(([href, label]) => <Link key={href} href={href}>{label}</Link>)}</nav>}
      {!allowed ? <section className="panel"><p className="error-text">Developer veya admin yetkisi gerekiyor.</p></section> : children}
    </main>
  );
}
