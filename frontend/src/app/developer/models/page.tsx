"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { api } from "@/lib/api";

export default function ModelsPage() {
  const models = useQuery({ queryKey: ["models-page"], queryFn: () => api.models({ limit: 200 }) });
  return <DeveloperShell title="Model registry" description="Model sürümlerini, durumlarını ve metriklerini inceleyin."><section className="panel"><div className="table-wrap"><table className="data-table"><thead><tr><th>ID</th><th>Sürüm</th><th>Enerji</th><th>Durum</th><th>MAE</th><th>R²</th><th>Detay</th></tr></thead><tbody>{models.data?.map((model) => <tr key={model.id}><td>#{model.id}</td><td>{model.model_version}</td><td>{model.energy_type.toUpperCase()}</td><td>{model.status}</td><td>{model.metrics.mae?.toFixed(3) ?? "—"}</td><td>{model.metrics.r2?.toFixed(3) ?? "—"}</td><td><Link href={`/developer/models/${model.id}`}>Aç</Link></td></tr>)}</tbody></table></div>{models.error && <p className="error-text">{(models.error as Error).message}</p>}</section></DeveloperShell>;
}
