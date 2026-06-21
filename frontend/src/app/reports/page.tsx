"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AuthPanel } from "@/components/AuthPanel";
import { useAuthSession } from "@/hooks/useAuthSession";
import { api } from "@/lib/api";

export default function ReportsPage() {
  const session = useAuthSession();
  const history = useQuery({ queryKey: ["report-history"], queryFn: api.reportHistory, enabled: !!session });
  return <main className="page-shell"><Link href="/" className="back-link">← Ana sayfa</Link><header className="hero-header"><div><h1>Rapor geçmişi</h1><p className="muted">Oluşturduğunuz ilçe analiz raporlarına yeniden erişin.</p></div></header><AuthPanel /><section className="panel">{!session ? <p>Rapor geçmişi için giriş yapın.</p> : <div className="card-list">{history.data?.map((report, index) => <article className="mini-card" key={`${report.created_at}-${index}`}><strong>{report.district_name}</strong><p className="muted compact">{report.energy.toUpperCase()} · {new Date(report.created_at).toLocaleString("tr-TR")}</p><button type="button" onClick={() => api.downloadReport(report.district_id, report.energy)}>PDF indir</button></article>)}{history.data?.length === 0 && <p className="muted">Henüz rapor üretilmedi.</p>}</div>}{history.error && <p className="error-text">{(history.error as Error).message}</p>}</section></main>;
}
