"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { api } from "@/lib/api";

export default function ModelDetailPage() {
  const id = Number(useParams<{ id: string }>().id);
  const model = useQuery({ queryKey: ["model-detail", id], queryFn: () => api.modelDetail(id) });
  return <DeveloperShell title={`Model #${id}`} description="Artefakt, parametre, metrik ve özellik önem bilgileri."><section className="panel">{model.data && <><div className="dashboard-grid"><div><h2>{model.data.model_version}</h2><p>{model.data.energy_type.toUpperCase()} · {model.data.status}</p><pre className="mini-json">{JSON.stringify(model.data.metrics, null, 2)}</pre></div><div><h2>Parametreler</h2><pre className="mini-json">{JSON.stringify(model.data.parameters, null, 2)}</pre></div></div><h2>Feature importance</h2><div className="bar-list">{Object.entries(model.data.feature_importance).sort((a,b) => b[1]-a[1]).map(([name,value]) => <div className="bar-row" key={name}><span>{name}</span><div className="bar-track"><div className="bar-fill ges" style={{width:`${Math.min(100, Math.abs(value))}%`}} /></div><strong>{value.toFixed(3)}</strong></div>)}</div></>}{model.error && <p className="error-text">{(model.error as Error).message}</p>}</section></DeveloperShell>;
}
