"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { AuthPanel } from "@/components/AuthPanel";
import { api, getStoredSession, type AuthSession } from "@/lib/api";

export default function ProjectsPage() {
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

  const projects = useQuery({
    queryKey: ["projects-page-projects"],
    queryFn: api.listProjects,
    enabled: !!session,
  });
  const scenarios = useQuery({
    queryKey: ["projects-page-scenarios"],
    queryFn: api.listScenarios,
    enabled: !!session,
  });
  const deleteProject = useMutation({
    mutationFn: api.deleteProject,
    onSuccess: () => projects.refetch(),
  });

  return (
    <main className="page-shell">
      <Link href="/" className="back-link">
        ← Ana sayfa
      </Link>
      <header className="hero-header">
        <div>
          <h1>Projeler ve kayıtlı senaryolar</h1>
          <p className="muted">
            Kullanıcı testlerinde oluşturulan proje ve senaryo kayıtlarını doğrulayın.
          </p>
        </div>
      </header>
      <AuthPanel />

      {!session ? (
        <section className="panel">
          <p>Projeleri görmek için demo kullanıcı ile giriş yapın.</p>
        </section>
      ) : (
        <section className="dashboard-grid">
          <div className="panel">
            <div className="section-heading">
              <div>
                <h2>Projeler</h2>
                <p>{projects.data?.length ?? 0} kayıt</p>
              </div>
            </div>
            {projects.isLoading && <p className="muted">Projeler yükleniyor…</p>}
            {projects.error && (
              <p className="error-text">{(projects.error as Error).message}</p>
            )}
            <div className="card-list">
              {projects.data?.map((project) => (
                <article key={project.id} className="mini-card">
                  <strong>{project.name}</strong>
                  <p className="muted compact">
                    {project.energy.toUpperCase()} · {project.district_ids.length} ilçe
                  </p>
                  {project.note && <p>{project.note}</p>}
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => deleteProject.mutate(project.id)}
                  >
                    Sil
                  </button>
                </article>
              ))}
              {projects.data?.length === 0 && (
                <p className="muted">Henüz proje yok. İlçe detayından oluşturun.</p>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="section-heading">
              <div>
                <h2>Senaryolar</h2>
                <p>{scenarios.data?.length ?? 0} kayıt</p>
              </div>
            </div>
            {scenarios.error && (
              <p className="error-text">{(scenarios.error as Error).message}</p>
            )}
            <div className="card-list">
              {scenarios.data?.map((scenario) => (
                <article key={scenario.id} className="mini-card">
                  <div className="eyebrow">#{scenario.id}</div>
                  <strong>{scenario.district_id}</strong>
                  <p className="muted compact">
                    GES {scenario.result.scenario.ges.toFixed(1)} (
                    {scenario.result.delta_ges >= 0 ? "+" : ""}
                    {scenario.result.delta_ges.toFixed(2)}) · RES{" "}
                    {scenario.result.scenario.res.toFixed(1)} (
                    {scenario.result.delta_res >= 0 ? "+" : ""}
                    {scenario.result.delta_res.toFixed(2)})
                  </p>
                  <pre className="mini-json">
                    {JSON.stringify(scenario.overrides, null, 2)}
                  </pre>
                </article>
              ))}
              {scenarios.data?.length === 0 && (
                <p className="muted">Henüz kayıtlı senaryo yok.</p>
              )}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
