"use client";

import { useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { api } from "@/lib/api";

export default function DataQualityPage() {
  const quality = useQuery({ queryKey: ["data-quality-page"], queryFn: api.dataQualityLatest });
  return <DeveloperShell title="Veri kalitesi" description="Veri seti kalite kapıları, kaynaklar ve uyarılar."><section className="panel">{quality.data && <><div className="metric-card-grid">{[["Satır",quality.data.total_rows],["İlçe",quality.data.district_count],["Eksik",quality.data.missing_values],["Sıfır alan",quality.data.zero_area_count],["Aykırı",quality.data.outlier_count]].map(([label,value]) => <div className="mini-card" key={String(label)}><div className="eyebrow">{label}</div><div className="big-stat">{Number(value).toLocaleString("tr-TR")}</div></div>)}</div><h2>Uyarılar</h2>{quality.data.warnings.length ? <ul>{quality.data.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul> : <p className="success-text">Kalite uyarısı yok.</p>}</>}{quality.error && <p className="error-text">{(quality.error as Error).message}</p>}</section></DeveloperShell>;
}
