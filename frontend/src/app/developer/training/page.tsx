"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { DeveloperShell } from "@/components/DeveloperShell";
import { api, type Energy } from "@/lib/api";

export default function TrainingPage() {
  const [targets, setTargets] = useState<Energy[]>(["ges", "res"]);
  const [note, setNote] = useState("");
  const jobs = useQuery({ queryKey: ["training-page-jobs"], queryFn: () => api.trainingJobs(100), refetchInterval: 4000 });
  const start = useMutation({ mutationFn: () => api.createTrainingJob({ energy_targets: targets, note: note || null, quick_mode: true }), onSuccess: () => jobs.refetch() });
  const toggle = (energy: Energy) => setTargets((value) => value.includes(energy) ? value.filter((item) => item !== energy) : [...value, energy]);

  return <DeveloperShell title="Model eğitimleri" description="Yeni eğitim başlatın ve job yaşam döngüsünü izleyin.">
    <section className="panel"><h2>Yeni eğitim</h2><div className="form-grid"><fieldset><legend>Hedef</legend>{(["ges", "res"] as Energy[]).map((energy) => <label key={energy}><input type="checkbox" checked={targets.includes(energy)} onChange={() => toggle(energy)} /> {energy.toUpperCase()}</label>)}</fieldset><label className="field-stack form-wide"><span>Not</span><input value={note} onChange={(event) => setNote(event.target.value)} /></label><button type="button" disabled={!targets.length || start.isPending} onClick={() => start.mutate()}>Eğitimi başlat</button></div>{start.data && <p className="success-text">Eğitim #{start.data.id} oluşturuldu.</p>}</section>
    <section className="panel"><h2>Eğitim geçmişi</h2><div className="table-wrap"><table className="data-table"><thead><tr><th>ID</th><th>Durum</th><th>Hedef</th><th>Kullanıcı</th><th>Süre</th><th>Detay</th></tr></thead><tbody>{jobs.data?.map((job) => <tr key={job.id}><td>#{job.id}</td><td>{job.status}</td><td>{job.energy_targets.join(", ")}</td><td>{job.requested_by}</td><td>{job.duration_seconds?.toFixed(1) ?? "—"} sn</td><td><a href={`/developer/training/${job.id}`}>Aç</a></td></tr>)}</tbody></table></div></section>
  </DeveloperShell>;
}
