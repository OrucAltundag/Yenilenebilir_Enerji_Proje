"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { api } from "@/lib/api";

export default function TrainingDetailPage() {
  const id = Number(useParams<{ id: string }>().id);
  const job = useQuery({ queryKey: ["training-detail", id], queryFn: () => api.trainingJobDetail(id), refetchInterval: 3000 });
  return <DeveloperShell title={`Eğitim #${id}`} description="Parametreler, sonuçlar ve çalışma günlüğü."><section className="panel">{job.error ? <p className="error-text">{(job.error as Error).message}</p> : job.data && <div className="grid-2"><div><h2>{job.data.status}</h2><pre className="mini-json">{JSON.stringify(job.data.parameters, null, 2)}</pre><pre className="mini-json">{JSON.stringify(job.data.result_models, null, 2)}</pre></div><div><h2>Log</h2><pre className="log-view">{job.data.error_message || job.data.log_text || "Log yok."}</pre></div></div>}</section></DeveloperShell>;
}
