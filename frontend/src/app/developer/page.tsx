"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AuthPanel } from "@/components/AuthPanel";
import {
  api,
  getStoredSession,
  type AuthSession,
  type Energy,
  type ModelCompareResult,
  type ModelSummary,
  type Readyz,
  type TrainingJobDetail,
  type TrainingJobPayload,
} from "@/lib/api";

const ENERGY_LABEL: Record<Energy, string> = { ges: "GES", res: "RES" };

const STATUS_LABEL: Record<string, string> = {
  queued: "Sırada",
  running: "Çalışıyor",
  completed: "Tamamlandı",
  failed: "Hata",
  candidate: "Aday",
  active: "Aktif",
  archived: "Arşivli",
};

function statusClass(status: string): string {
  switch (status) {
    case "active":
    case "completed":
      return "status-ok";
    case "running":
    case "candidate":
      return "status-info";
    case "failed":
      return "status-error";
    case "archived":
      return "status-muted";
    default:
      return "status-warn";
  }
}

function formatMetric(value: number | undefined): string {
  if (value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(3);
}

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("tr-TR");
  } catch {
    return value;
  }
}

export default function DeveloperPage() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [compareLeftId, setCompareLeftId] = useState<number | null>(null);
  const [compareRightId, setCompareRightId] = useState<number | null>(null);

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

  const role = session?.role;
  const isAllowed = role === "developer" || role === "admin";

  const queryClient = useQueryClient();

  const jobs = useQuery({
    queryKey: ["ml-training-jobs"],
    queryFn: () => api.trainingJobs(20),
    enabled: isAllowed,
    refetchInterval: 4000,
  });

  const models = useQuery({
    queryKey: ["ml-models"],
    queryFn: () => api.models({ limit: 50 }),
    enabled: isAllowed,
  });

  const active = useQuery({
    queryKey: ["ml-active-models"],
    queryFn: api.activeModels,
    enabled: isAllowed,
  });

  const quality = useQuery({
    queryKey: ["ml-data-quality"],
    queryFn: api.dataQualityLatest,
    enabled: isAllowed,
  });

  const health = useQuery({
    queryKey: ["system-readyz"],
    queryFn: api.readyz,
    enabled: isAllowed,
    refetchInterval: 15000,
  });

  const selectedJob = useQuery({
    queryKey: ["ml-training-job", selectedJobId],
    queryFn: () => api.trainingJobDetail(selectedJobId as number),
    enabled: isAllowed && selectedJobId !== null,
    refetchInterval: (query) =>
      query.state.data?.status === "queued" || query.state.data?.status === "running"
        ? 3000
        : false,
  });

  const comparison = useQuery({
    queryKey: ["ml-model-compare", compareLeftId, compareRightId],
    queryFn: () => api.compareModels(compareLeftId as number, compareRightId as number),
    enabled:
      isAllowed &&
      compareLeftId !== null &&
      compareRightId !== null &&
      compareLeftId !== compareRightId,
  });

  const startJob = useMutation({
    mutationFn: (payload: TrainingJobPayload) => api.createTrainingJob(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-training-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ml-models"] });
    },
  });

  const candidate = useMutation({
    mutationFn: (id: number) => api.markModelCandidate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-models"] });
      queryClient.invalidateQueries({ queryKey: ["ml-active-models"] });
    },
  });

  const activate = useMutation({
    mutationFn: (id: number) => api.activateModel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-models"] });
      queryClient.invalidateQueries({ queryKey: ["ml-active-models"] });
    },
  });

  const archive = useMutation({
    mutationFn: (id: number) => api.archiveModel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-models"] });
      queryClient.invalidateQueries({ queryKey: ["ml-active-models"] });
    },
  });

  const lastJob = jobs.data?.[0];

  useEffect(() => {
    if (lastJob?.status === "completed" || lastJob?.status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["ml-models"] });
      queryClient.invalidateQueries({ queryKey: ["ml-active-models"] });
    }
  }, [lastJob?.id, lastJob?.status, queryClient]);

  const activeGes = useMemo(
    () => active.data?.find((m) => m.energy_type === "ges"),
    [active.data]
  );
  const activeRes = useMemo(
    () => active.data?.find((m) => m.energy_type === "res"),
    [active.data]
  );

  return (
    <main className="page-shell">
      <Link href="/" className="back-link">
        ← Ana sayfa
      </Link>
      <header className="hero-header">
        <div>
          <h1>Yazılımcı paneli</h1>
          <p className="muted">
            Model eğitimi, veri kalitesi, sistem sağlığı ve model sürüm yönetimi.
          </p>
        </div>
      </header>
      <AuthPanel />

      {!isAllowed ? (
        <section className="panel">
          <p className="error-text">
            Bu panel için developer veya admin yetkisi gerekiyor.
            developer/developer123 ile giriş yapın.
          </p>
        </section>
      ) : (
        <>
          {/* Durum kartları */}
          <section className="dashboard-grid">
            <StatusCard
              title="Aktif GES modeli"
              version={activeGes?.model_version}
              note={
                activeGes
                  ? `R²: ${formatMetric(activeGes.metrics.r2)} · MAE: ${formatMetric(activeGes.metrics.mae)}`
                  : "Atanmadı"
              }
              tone={activeGes ? "ok" : "warn"}
            />
            <StatusCard
              title="Aktif RES modeli"
              version={activeRes?.model_version}
              note={
                activeRes
                  ? `R²: ${formatMetric(activeRes.metrics.r2)} · MAE: ${formatMetric(activeRes.metrics.mae)}`
                  : "Atanmadı"
              }
              tone={activeRes ? "ok" : "warn"}
            />
            <StatusCard
              title="Veri seti"
              version={quality.data?.dataset_version}
              note={
                quality.data
                  ? `${quality.data.total_rows.toLocaleString("tr-TR")} satır · ${quality.data.district_count} ilçe`
                  : "Yükleniyor"
              }
              tone={quality.data?.warnings.length ? "warn" : "ok"}
            />
            <StatusCard
              title="Son eğitim"
              version={lastJob ? `#${lastJob.id}` : "—"}
              note={
                lastJob
                  ? `${STATUS_LABEL[lastJob.status] ?? lastJob.status} · ${formatTimestamp(lastJob.created_at)}`
                  : "Henüz çalıştırılmadı"
              }
              tone={
                lastJob?.status === "failed"
                  ? "error"
                  : lastJob?.status === "running"
                  ? "info"
                  : "ok"
              }
            />
            <StatusCard
              title="Sistem durumu"
              version={health.data?.ready ? "Hazır" : "Kontrol gerekli"}
              note={health.data ? `${Object.values(health.data.checks).filter(Boolean).length}/${Object.keys(health.data.checks).length} kontrol başarılı` : "API bekleniyor"}
              tone={health.data?.ready ? "ok" : health.error ? "error" : "warn"}
            />
          </section>

          {/* Eğitim formu */}
          <TrainingForm
            isPending={startJob.isPending}
            error={(startJob.error as Error | null)?.message}
            success={startJob.data ? `Eğitim #${startJob.data.id} kuyruğa alındı.` : undefined}
            onSubmit={(payload) => startJob.mutate(payload)}
          />

          {/* Eğitim job tablosu */}
          <section className="panel">
            <h2>Eğitim geçmişi</h2>
            {jobs.error ? (
              <p className="error-text">{(jobs.error as Error).message}</p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Durum</th>
                      <th>Hedefler</th>
                      <th>İsteyen</th>
                      <th>Süre</th>
                      <th>Oluşturma</th>
                      <th>Not</th>
                      <th>Aksiyon</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.data?.map((job) => (
                      <tr key={job.id}>
                        <td>#{job.id}</td>
                        <td>
                          <span className={`pill ${statusClass(job.status)}`}>
                            {STATUS_LABEL[job.status] ?? job.status}
                          </span>
                        </td>
                        <td>{job.energy_targets.map((e) => ENERGY_LABEL[e as Energy] ?? e).join(", ")}</td>
                        <td>{job.requested_by}</td>
                        <td>
                          {job.duration_seconds != null
                            ? `${job.duration_seconds.toFixed(1)} sn`
                            : "—"}
                        </td>
                        <td>{formatTimestamp(job.created_at)}</td>
                        <td className="muted">{job.note ?? "—"}</td>
                        <td>
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={() => setSelectedJobId(job.id)}
                          >
                            Detay
                          </button>
                        </td>
                      </tr>
                    ))}
                    {jobs.data?.length === 0 && (
                      <tr>
                        <td colSpan={8} className="muted">
                          Henüz eğitim job yok.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {selectedJobId !== null && (
            <JobDetailPanel
              job={selectedJob.data}
              loading={selectedJob.isLoading}
              error={(selectedJob.error as Error | null)?.message}
              onClose={() => setSelectedJobId(null)}
            />
          )}

          {/* Model registry */}
          <section className="panel">
            <h2>Model registry</h2>
            {models.error ? (
              <p className="error-text">{(models.error as Error).message}</p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Sürüm</th>
                      <th>Enerji</th>
                      <th>Durum</th>
                      <th>MAE</th>
                      <th>RMSE</th>
                      <th>R²</th>
                      <th>Oluşturan</th>
                      <th>Tarih</th>
                      <th>Aksiyon</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.data?.map((model) => (
                      <ModelRow
                        key={model.id}
                        model={model}
                        role={role}
                        onCandidate={() => candidate.mutate(model.id)}
                        onActivate={() => activate.mutate(model.id)}
                        onArchive={() => archive.mutate(model.id)}
                        busy={
                          candidate.isPending || activate.isPending || archive.isPending
                        }
                      />
                    ))}
                    {models.data?.length === 0 && (
                      <tr>
                        <td colSpan={10} className="muted">
                          Kayıtlı model yok. Yeni eğitim başlatın.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
            {(candidate.error || activate.error || archive.error) && (
              <p className="error-text">
                {(
                  (candidate.error || activate.error || archive.error) as Error
                ).message}
              </p>
            )}
          </section>

          <ModelComparisonPanel
            models={models.data ?? []}
            leftId={compareLeftId}
            rightId={compareRightId}
            result={comparison.data}
            loading={comparison.isFetching}
            error={(comparison.error as Error | null)?.message}
            onLeftChange={setCompareLeftId}
            onRightChange={setCompareRightId}
          />

          {/* Veri kalitesi */}
          <section className="panel">
            <h2>Veri kalitesi</h2>
            {quality.error ? (
              <p className="error-text">{(quality.error as Error).message}</p>
            ) : quality.data ? (
              <div className="grid-2">
                <ul className="kv-list">
                  <li>
                    <span>Toplam satır</span>
                    <strong>{quality.data.total_rows.toLocaleString("tr-TR")}</strong>
                  </li>
                  <li>
                    <span>İlçe sayısı</span>
                    <strong>{quality.data.district_count}</strong>
                  </li>
                  <li>
                    <span>Eksik değer</span>
                    <strong>{quality.data.missing_values}</strong>
                  </li>
                  <li>
                    <span>Sıfır alan</span>
                    <strong>{quality.data.zero_area_count}</strong>
                  </li>
                  <li>
                    <span>Aykırı değer</span>
                    <strong>{quality.data.outlier_count}</strong>
                  </li>
                  <li>
                    <span>Veri seti</span>
                    <strong>{quality.data.dataset_version}</strong>
                  </li>
                </ul>
                <div>
                  <strong>Uyarılar</strong>
                  {quality.data.warnings.length === 0 ? (
                    <p className="muted compact">Uyarı yok.</p>
                  ) : (
                    <ul className="warn-list">
                      {quality.data.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : (
              <p className="muted">Yükleniyor…</p>
            )}
          </section>

          <SystemHealthPanel
            health={health.data}
            loading={health.isLoading}
            error={(health.error as Error | null)?.message}
            onRefresh={() => health.refetch()}
          />
        </>
      )}
    </main>
  );
}

function JobDetailPanel({
  job,
  loading,
  error,
  onClose,
}: {
  job: TrainingJobDetail | undefined;
  loading: boolean;
  error: string | undefined;
  onClose: () => void;
}) {
  return (
    <section className="panel detail-panel" aria-live="polite">
      <div className="section-heading">
        <div>
          <h2>Eğitim detayı {job ? `#${job.id}` : ""}</h2>
          <p>Parametreler, üretilen modeller ve çalışma günlüğü.</p>
        </div>
        <button type="button" className="ghost-button" onClick={onClose}>
          Kapat
        </button>
      </div>
      {loading ? (
        <p className="muted">Detay yükleniyor…</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : job ? (
        <div className="grid-2">
          <div>
            <ul className="kv-list">
              <li><span>Durum</span><strong>{STATUS_LABEL[job.status] ?? job.status}</strong></li>
              <li><span>Veri seti</span><strong>{job.dataset_version ?? "—"}</strong></li>
              <li><span>Başlangıç</span><strong>{formatTimestamp(job.started_at)}</strong></li>
              <li><span>Bitiş</span><strong>{formatTimestamp(job.finished_at)}</strong></li>
              <li><span>Süre</span><strong>{job.duration_seconds != null ? `${job.duration_seconds.toFixed(1)} sn` : "—"}</strong></li>
            </ul>
            <h3>Parametreler</h3>
            <pre className="mini-json">{JSON.stringify(job.parameters, null, 2)}</pre>
          </div>
          <div>
            <h3>Sonuç modelleri</h3>
            <pre className="mini-json">{JSON.stringify(job.result_models, null, 2)}</pre>
            <h3>Çalışma günlüğü</h3>
            <pre className="log-view">{job.error_message || job.log_text || "Günlük kaydı yok."}</pre>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ModelComparisonPanel({
  models,
  leftId,
  rightId,
  result,
  loading,
  error,
  onLeftChange,
  onRightChange,
}: {
  models: ModelSummary[];
  leftId: number | null;
  rightId: number | null;
  result: ModelCompareResult | undefined;
  loading: boolean;
  error: string | undefined;
  onLeftChange: (id: number | null) => void;
  onRightChange: (id: number | null) => void;
}) {
  const renderOptions = (excluded: number | null) =>
    models.filter((model) => model.id !== excluded).map((model) => (
      <option key={model.id} value={model.id}>
        #{model.id} · {ENERGY_LABEL[model.energy_type]} · {model.model_version}
      </option>
    ));

  const metricNames = result
    ? Array.from(new Set([...Object.keys(result.left.metrics), ...Object.keys(result.right.metrics)]))
    : [];

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <h2>Model karşılaştırma</h2>
          <p>İki modelin metriklerini ve özellik önem farklarını karşılaştırın.</p>
        </div>
      </div>
      <div className="compare-selectors">
        <label className="field-stack">
          <span>Model A</span>
          <select value={leftId ?? ""} onChange={(e) => onLeftChange(e.target.value ? Number(e.target.value) : null)}>
            <option value="">Model seçin</option>
            {renderOptions(rightId)}
          </select>
        </label>
        <label className="field-stack">
          <span>Model B</span>
          <select value={rightId ?? ""} onChange={(e) => onRightChange(e.target.value ? Number(e.target.value) : null)}>
            <option value="">Model seçin</option>
            {renderOptions(leftId)}
          </select>
        </label>
      </div>
      {loading && <p className="muted">Karşılaştırma yükleniyor…</p>}
      {error && <p className="error-text">{error}</p>}
      {result && (
        <div className="grid-2">
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Metrik</th><th>A</th><th>B</th><th>Fark</th></tr></thead>
              <tbody>
                {metricNames.map((name) => (
                  <tr key={name}>
                    <td>{name.toUpperCase()}</td>
                    <td>{formatMetric(result.left.metrics[name])}</td>
                    <td>{formatMetric(result.right.metrics[name])}</td>
                    <td>{formatMetric(result.metric_diff[name])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <h3>En çok değişen özellikler</h3>
            <ol className="feature-diff-list">
              {Object.entries(result.feature_importance_diff)
                .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                .slice(0, 10)
                .map(([feature, difference]) => (
                  <li key={feature}><span>{feature}</span><strong>{difference > 0 ? "+" : ""}{formatMetric(difference)}</strong></li>
                ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}

function SystemHealthPanel({
  health,
  loading,
  error,
  onRefresh,
}: {
  health: Readyz | undefined;
  loading: boolean;
  error: string | undefined;
  onRefresh: () => void;
}) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div><h2>Sistem sağlığı</h2><p>API, veri ve model hazır olma kontrolleri.</p></div>
        <button type="button" className="ghost-button" onClick={onRefresh} disabled={loading}>Yenile</button>
      </div>
      {error ? <p className="error-text">{error}</p> : health ? (
        <div className="health-grid">
          {Object.entries(health.checks).map(([name, ok]) => (
            <div className="health-check" key={name}>
              <span>{name.replaceAll("_", " ")}</span>
              <span className={`pill ${ok ? "status-ok" : "status-error"}`}>{ok ? "Başarılı" : "Hata"}</span>
            </div>
          ))}
        </div>
      ) : <p className="muted">Kontroller yükleniyor…</p>}
    </section>
  );
}

function StatusCard({
  title,
  version,
  note,
  tone,
}: {
  title: string;
  version: string | undefined;
  note: string;
  tone: "ok" | "info" | "warn" | "error";
}) {
  return (
    <div className={`panel status-card status-tone-${tone}`}>
      <div className="eyebrow">{title}</div>
      <div className="big-stat" title={version ?? "—"}>
        {version ?? "—"}
      </div>
      <p className="muted compact">{note}</p>
    </div>
  );
}

function TrainingForm({
  isPending,
  error,
  success,
  onSubmit,
}: {
  isPending: boolean;
  error: string | undefined;
  success: string | undefined;
  onSubmit: (payload: TrainingJobPayload) => void;
}) {
  const [ges, setGes] = useState(true);
  const [res, setRes] = useState(true);
  const [testSize, setTestSize] = useState(0.2);
  const [nEstimators, setNEstimators] = useState(200);
  const [maxDepth, setMaxDepth] = useState(6);
  const [learningRate, setLearningRate] = useState(0.05);
  const [randomState, setRandomState] = useState(42);
  const [quick, setQuick] = useState(true);
  const [note, setNote] = useState("");

  return (
    <section className="panel">
      <h2>Yeni eğitim başlat</h2>
      <p className="muted compact">
        Eğitim arka planda çalışır. Tamamlandığında model registry&apos;de
        &quot;completed&quot; statüsüyle görünür.
      </p>
      <form
        className="form-grid"
        onSubmit={(event) => {
          event.preventDefault();
          const targets: Energy[] = [];
          if (ges) targets.push("ges");
          if (res) targets.push("res");
          if (targets.length === 0) return;
          onSubmit({
            energy_targets: targets,
            test_size: testSize,
            random_state: randomState,
            n_estimators: nEstimators,
            learning_rate: learningRate,
            max_depth: maxDepth,
            quick_mode: quick,
            note: note || null,
          });
        }}
      >
        <fieldset>
          <legend>Hedef enerji</legend>
          <label>
            <input
              type="checkbox"
              checked={ges}
              onChange={(e) => setGes(e.target.checked)}
            />{" "}
            GES
          </label>
          <label>
            <input
              type="checkbox"
              checked={res}
              onChange={(e) => setRes(e.target.checked)}
            />{" "}
            RES
          </label>
        </fieldset>
        <label className="field-stack">
          <span>Test oranı</span>
          <input
            type="number"
            min={0.05}
            max={0.5}
            step={0.05}
            value={testSize}
            onChange={(e) => setTestSize(Number(e.target.value))}
          />
        </label>
        <label className="field-stack">
          <span>n_estimators</span>
          <input
            type="number"
            min={10}
            max={5000}
            step={10}
            value={nEstimators}
            onChange={(e) => setNEstimators(Number(e.target.value))}
          />
        </label>
        <label className="field-stack">
          <span>max_depth</span>
          <input
            type="number"
            min={1}
            max={12}
            value={maxDepth}
            onChange={(e) => setMaxDepth(Number(e.target.value))}
          />
        </label>
        <label className="field-stack">
          <span>learning_rate</span>
          <input
            type="number"
            min={0.001}
            max={1}
            step={0.001}
            value={learningRate}
            onChange={(e) => setLearningRate(Number(e.target.value))}
          />
        </label>
        <label className="field-stack">
          <span>random_state</span>
          <input
            type="number"
            value={randomState}
            onChange={(e) => setRandomState(Number(e.target.value))}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={quick}
            onChange={(e) => setQuick(e.target.checked)}
          />{" "}
          Hızlı eğitim (örneklenmiş veri)
        </label>
        <label className="field-stack form-wide">
          <span>Not</span>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="ör. hyperparam tuning denemesi"
          />
        </label>
        <div className="form-wide button-row">
          <button type="submit" disabled={isPending || (!ges && !res)}>
            {isPending ? "Başlatılıyor…" : "Yeni Eğitimi Başlat"}
          </button>
          {!ges && !res && <span className="error-text">En az bir enerji türü seçin.</span>}
          {success && <span className="success-text">{success}</span>}
          {error && <span className="error-text">{error}</span>}
        </div>
      </form>
    </section>
  );
}

function ModelRow({
  model,
  role,
  onCandidate,
  onActivate,
  onArchive,
  busy,
}: {
  model: ModelSummary;
  role: string | undefined;
  onCandidate: () => void;
  onActivate: () => void;
  onArchive: () => void;
  busy: boolean;
}) {
  const isAdmin = role === "admin";
  return (
    <tr>
      <td>#{model.id}</td>
      <td title={model.model_version}>{model.model_version.slice(0, 22)}…</td>
      <td>{ENERGY_LABEL[model.energy_type as Energy] ?? model.energy_type}</td>
      <td>
        <span className={`pill ${statusClass(model.status)}`}>
          {STATUS_LABEL[model.status] ?? model.status}
        </span>
      </td>
      <td>{formatMetric(model.metrics.mae)}</td>
      <td>{formatMetric(model.metrics.rmse)}</td>
      <td>{formatMetric(model.metrics.r2)}</td>
      <td>{model.created_by}</td>
      <td>{formatTimestamp(model.created_at)}</td>
      <td>
        <div className="button-row compact">
          {(model.status === "completed" || model.status === "archived") && (
            <button
              type="button"
              className="ghost-button"
              onClick={onCandidate}
              disabled={busy}
            >
              Aday yap
            </button>
          )}
          {isAdmin &&
            (model.status === "candidate" || model.status === "completed") && (
              <button type="button" onClick={onActivate} disabled={busy}>
                Aktif
              </button>
            )}
          {isAdmin && model.status !== "archived" && model.status !== "active" && (
            <button
              type="button"
              className="ghost-button"
              onClick={onArchive}
              disabled={busy}
            >
              Arşivle
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
