"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { useAuthSession } from "@/hooks/useAuthSession";
import { api } from "@/lib/api";

export default function ApprovalsPage() {
  const session = useAuthSession();
  const approvals = useQuery({ queryKey: ["model-approvals"], queryFn: api.modelApprovals });
  const activate = useMutation({ mutationFn: (id: number) => api.activateModel(id), onSuccess: () => approvals.refetch() });
  return <DeveloperShell title="Model onayları" description="Developer adaylarını inceleyin; yalnız admin canlıya alabilir."><section className="panel">{session?.role !== "admin" && <p className="muted">Adayları görebilirsiniz; aktivasyon admin yetkisi gerektirir.</p>}<div className="card-list">{approvals.data?.map((model) => <article className="mini-card" key={model.id}><strong>#{model.id} · {model.model_version}</strong><p>{model.energy_type.toUpperCase()} · MAE {model.metrics.mae?.toFixed(3) ?? "—"} · R² {model.metrics.r2?.toFixed(3) ?? "—"}</p>{session?.role === "admin" && <button type="button" disabled={activate.isPending} onClick={() => activate.mutate(model.id)}>Aktif yap</button>}</article>)}</div>{approvals.data?.length === 0 && <p className="muted">Onay bekleyen model yok.</p>}{approvals.error && <p className="error-text">{(approvals.error as Error).message}</p>}</section></DeveloperShell>;
}
