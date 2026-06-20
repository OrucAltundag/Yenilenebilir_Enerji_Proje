"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import {
  api,
  getStoredSession,
  type AuthSession,
  type DistrictSummary,
  type Energy,
  type Project,
} from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";

type OverrideKey =
  | "ALLSKY_SFC_SW_DWN"
  | "WS10M"
  | "arazi_egimi_yuzde"
  | "tesvik_bolgesi";

const INPUTS: {
  key: OverrideKey;
  label: string;
  min: number;
  max: number;
  step: number;
  suffix: string;
}[] = [
  {
    key: "ALLSKY_SFC_SW_DWN",
    label: "Güneş ışınımı",
    min: 0,
    max: 12,
    step: 0.1,
    suffix: "kWh/m²",
  },
  { key: "WS10M", label: "Rüzgâr hızı", min: 0, max: 25, step: 0.1, suffix: "m/s" },
  {
    key: "arazi_egimi_yuzde",
    label: "Arazi eğimi",
    min: 0,
    max: 90,
    step: 0.1,
    suffix: "%",
  },
  { key: "tesvik_bolgesi", label: "Teşvik bölgesi", min: 1, max: 6, step: 1, suffix: "" },
];

export function ScenarioLab({
  summary,
  energy,
}: {
  summary: DistrictSummary;
  energy: Energy;
}) {
  const [projectName, setProjectName] = useState(
    `${summary.province} / ${summary.district} analizi`
  );
  const [selectedProject, setSelectedProject] = useState<number | "new" | "none">(
    "none"
  );
  const [session, setSession] = useState<AuthSession | null>(null);
  const [values, setValues] = useState<Record<OverrideKey, number>>(() => ({
    ALLSKY_SFC_SW_DWN: summary.features.ALLSKY_SFC_SW_DWN,
    WS10M: summary.features.WS10M,
    arazi_egimi_yuzde: summary.features.arazi_egimi_yuzde,
    tesvik_bolgesi: summary.features.tesvik_bolgesi,
  }));

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
    queryKey: ["projects"],
    queryFn: api.listProjects,
    enabled: !!session,
  });

  const overrides = useMemo(() => {
    return Object.fromEntries(
      INPUTS.filter((input) => values[input.key] !== summary.features[input.key]).map(
        (input) => [input.key, values[input.key]]
      )
    ) as Record<string, number>;
  }, [summary.features, values]);

  const simulate = useMutation({
    mutationFn: () => api.simulate(summary.district_id, overrides),
  });

  const createProject = useMutation({
    mutationFn: () =>
      api.createProject({
        name: projectName,
        note: "Kullanıcı testi sırasında oluşturuldu.",
        district_ids: [summary.district_id],
        energy,
      }),
    onSuccess: (project) => {
      setSelectedProject(project.id);
      projects.refetch();
    },
  });

  const saveScenario = useMutation({
    mutationFn: async () => {
      let projectId: number | null =
        typeof selectedProject === "number" ? selectedProject : null;
      if (selectedProject === "new") {
        const project = await api.createProject({
          name: projectName,
          note: "Senaryo kaydı için otomatik oluşturuldu.",
          district_ids: [summary.district_id],
          energy,
        });
        projectId = project.id;
      }
      return api.saveScenario({
        district_id: summary.district_id,
        overrides,
        project_id: projectId,
      });
    },
    onSuccess: () => {
      projects.refetch();
    },
  });

  const report = useMutation({
    mutationFn: () => api.downloadReport(summary.district_id, energy),
    onSuccess: ({ blob, filename }) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
  });

  const scenarioScore =
    energy === "ges"
      ? simulate.data?.scenario_ges ?? summary.ges_score_mean
      : simulate.data?.scenario_res ?? summary.res_score_mean;
  const delta =
    energy === "ges" ? simulate.data?.delta_ges ?? 0 : simulate.data?.delta_res ?? 0;

  return (
    <div className="scenario-grid">
      <div>
        <div className="section-heading">
          <div>
            <h3>Senaryo simülasyonu</h3>
            <p>Değerleri değiştirip skordaki etkisini test edin.</p>
          </div>
          <button
            type="button"
            onClick={() => simulate.mutate()}
            disabled={simulate.isPending}
          >
            {simulate.isPending ? "Hesaplanıyor…" : "Simüle et"}
          </button>
        </div>

        <div className="slider-list">
          {INPUTS.map((input) => (
            <label key={input.key} className="slider-row">
              <span>{input.label}</span>
              <input
                type="range"
                min={input.min}
                max={input.max}
                step={input.step}
                value={values[input.key]}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    [input.key]: Number(event.target.value),
                  }))
                }
              />
              <input
                aria-label={`${input.label} değeri`}
                type="number"
                min={input.min}
                max={input.max}
                step={input.step}
                value={values[input.key]}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    [input.key]: Number(event.target.value),
                  }))
                }
              />
              <small>{input.suffix}</small>
            </label>
          ))}
        </div>
      </div>

      <aside className="panel nested-panel">
        <div className="eyebrow">Senaryo sonucu</div>
        <div className="result-row">
          <span>Mevcut skor</span>
          <ScoreBadge
            score={energy === "ges" ? summary.ges_score_mean : summary.res_score_mean}
          />
        </div>
        <div className="result-row">
          <span>Yeni skor</span>
          <ScoreBadge score={scenarioScore} />
        </div>
        <div className={`delta ${delta >= 0 ? "positive" : "negative"}`}>
          {delta >= 0 ? "+" : ""}
          {delta.toFixed(2)} puan
        </div>

        <button
          type="button"
          className="wide-button"
          onClick={() => report.mutate()}
          disabled={report.isPending}
        >
          {report.isPending ? "PDF hazırlanıyor…" : "PDF raporu indir"}
        </button>
        {report.error && <p className="error-text">{(report.error as Error).message}</p>}
      </aside>

      <div className="panel nested-panel scenario-save">
        <div className="section-heading">
          <div>
            <h3>Kaydet</h3>
            <p>Analizleri kullanıcı testinde geri çağırmak için saklayın.</p>
          </div>
        </div>

        {!session ? (
          <p className="muted">
            Kaydetmek için üstte demo kullanıcı ile giriş yapın. Simülasyon ve PDF
            indirme girişsiz de çalışır.
          </p>
        ) : (
          <>
            <input
              aria-label="Proje adı"
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
            />
            <select
              aria-label="Senaryo proje seçimi"
              value={selectedProject}
              onChange={(event) => {
                const value = event.target.value;
                setSelectedProject(
                  value === "none" || value === "new" ? value : Number(value)
                );
              }}
            >
              <option value="none">Projesiz kaydet</option>
              <option value="new">Yeni proje oluştur</option>
              {projects.data?.map((project: Project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
            <div className="button-row">
              <button
                type="button"
                onClick={() => createProject.mutate()}
                disabled={createProject.isPending}
              >
                Proje oluştur
              </button>
              <button
                type="button"
                onClick={() => saveScenario.mutate()}
                disabled={saveScenario.isPending}
              >
                Senaryoyu kaydet
              </button>
            </div>
            {(createProject.isSuccess || saveScenario.isSuccess) && (
              <p className="success-text">Kayıt tamamlandı.</p>
            )}
            {(createProject.error || saveScenario.error) && (
              <p className="error-text">
                {((createProject.error || saveScenario.error) as Error).message}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
