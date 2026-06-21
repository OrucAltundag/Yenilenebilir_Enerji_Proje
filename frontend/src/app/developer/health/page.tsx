"use client";

import { useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { api } from "@/lib/api";

export default function HealthPage() {
  const health = useQuery({ queryKey: ["health-page"], queryFn: api.readyz, refetchInterval: 15000 });
  return <DeveloperShell title="Sistem sağlığı" description="API, veri, geometri ve model hazır olma kontrolleri."><section className="panel">{health.data && <><p className={`big-stat ${health.data.ready ? "success-text" : "error-text"}`}>{health.data.ready ? "Sistem hazır" : "Kontrol gerekli"}</p><div className="health-grid">{Object.entries(health.data.checks).map(([name,ok]) => <div className="health-check" key={name}><span>{name.replaceAll("_"," ")}</span><strong>{ok ? "Başarılı" : "Hata"}</strong></div>)}</div></>}{health.error && <p className="error-text">{(health.error as Error).message}</p>}</section></DeveloperShell>;
}
