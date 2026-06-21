"use client";

import Link from "next/link";
import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AuthPanel } from "@/components/AuthPanel";
import { EnergyToggle } from "@/components/EnergyToggle";
import { MonthlyChart } from "@/components/MonthlyChart";
import { ScenarioLab } from "@/components/ScenarioLab";
import { ScoreBadge } from "@/components/ScoreBadge";
import { ShapPanel } from "@/components/ShapPanel";
import { api, type Energy } from "@/lib/api";

const FEATURE_LABELS: Record<string, string> = {
  ALLSKY_SFC_SW_DWN: "Güneş ışınımı (kWh/m²)",
  WS10M: "Rüzgâr hızı (m/s)",
  T2M: "Sıcaklık (°C)",
  RH2M: "Nem (%)",
  arazi_egimi_yuzde: "Arazi eğimi (%)",
  yuzey_alani_km2: "Yüzölçümü (km²)",
  tesvik_bolgesi: "Teşvik bölgesi",
};

export default function DistrictPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [energy, setEnergy] = useState<Energy>("ges");

  const { data, isLoading, error } = useQuery({
    queryKey: ["summary", id],
    queryFn: () => api.summary(id),
  });

  if (isLoading) return <main style={{ padding: 32 }}>Yükleniyor…</main>;
  if (error || !data)
    return <main style={{ padding: 32 }}>İlçe bulunamadı.</main>;

  const score = energy === "ges" ? data.ges_score_mean : data.res_score_mean;
  const rank = energy === "ges" ? data.national_rank_ges : data.national_rank_res;
  const pct = energy === "ges" ? data.percentile_ges : data.percentile_res;

  return (
    <main style={{ maxWidth: 880, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <Link href="/" style={{ color: "var(--color-accent-res)", fontSize: 14 }}>
        ← Sıralamaya dön
      </Link>

      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "12px 0 20px" }}>
        <div>
          <h1 style={{ margin: 0 }}>
            {data.province} / {data.district}
          </h1>
          <p style={{ opacity: 0.7, margin: "4px 0 0" }}>{data.year} yıllık ortalaması</p>
        </div>
        <EnergyToggle value={energy} onChange={setEnergy} />
      </header>

      <AuthPanel />

      <section style={{ display: "flex", gap: 24, marginBottom: 24 }}>
        <Stat label="Skor" value={<ScoreBadge score={score} />} />
        <Stat label="Ulusal sıra" value={`${rank} / 957`} />
        <Stat label="Yüzdelik" value={`%${pct.toFixed(0)}`} />
      </section>

      <Card title="Aylık Profil">
        <MonthlyChart data={data.monthly} />
      </Card>

      <Card title="Açıklama (SHAP)">
        <ShapPanel districtId={id} energy={energy} />
      </Card>

      <Card title="Senaryo ve rapor">
        <ScenarioLab summary={data} energy={energy} />
      </Card>

      <Card title="Girdiler">
        <table style={{ width: "100%", fontSize: 14, borderCollapse: "collapse" }}>
          <tbody>
            {Object.entries(FEATURE_LABELS).map(([key, label]) => (
              <tr key={key} style={{ borderTop: "1px solid #233" }}>
                <td style={{ padding: 8, opacity: 0.7 }}>{label}</td>
                <td style={{ padding: 8, textAlign: "right" }}>
                  {data.features[key]?.toFixed(2) ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <p style={{ fontSize: 11, opacity: 0.5, marginTop: 16 }}>
        Veri sürümü {data.data_version} · Metodoloji {data.scoring_version}. Bu skor
        yatırım tavsiyesi değildir.
      </p>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontSize: 12, opacity: 0.6 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{value}</div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section
      style={{
        background: "var(--color-surface)",
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>{title}</h3>
      {children}
    </section>
  );
}
