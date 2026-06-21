"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AuthPanel } from "@/components/AuthPanel";
import { api } from "@/lib/api";

export default function DistrictComparePage() {
  const [ids, setIds] = useState("");
  const compare = useMutation({ mutationFn: () => api.compareDistricts(ids.split(",").map((id) => id.trim()).filter(Boolean)) });
  return <main className="page-shell"><Link href="/" className="back-link">← Ana sayfa</Link><header className="hero-header"><div><h1>İlçe karşılaştırma</h1><p className="muted">2–5 ilçenin GES/RES skorlarını ve temel girdilerini yan yana inceleyin.</p></div></header><AuthPanel /><section className="panel"><label className="field-stack"><span>İlçe kimlikleri (virgülle)</span><input value={ids} onChange={(event) => setIds(event.target.value)} placeholder="örn. 63-... , 06-..." /></label><button type="button" onClick={() => compare.mutate()} disabled={compare.isPending}>Karşılaştır</button>{compare.error && <p className="error-text">{(compare.error as Error).message}</p>}</section>{compare.data && <section className="panel"><div className="table-wrap"><table className="data-table"><thead><tr><th>İl / İlçe</th><th>GES</th><th>GES sıra</th><th>RES</th><th>RES sıra</th><th>Teşvik</th></tr></thead><tbody>{compare.data.map((item) => <tr key={item.district_id}><td><Link href={`/district/${item.district_id}`}>{item.province} / {item.district}</Link></td><td>{item.ges_score_mean?.toFixed(2)}</td><td>{item.national_rank_ges}</td><td>{item.res_score_mean?.toFixed(2)}</td><td>{item.national_rank_res}</td><td>{item.features.tesvik_bolgesi}</td></tr>)}</tbody></table></div></section>}</main>;
}
