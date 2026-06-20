"use client";

import { useQuery } from "@tanstack/react-query";

import { api, type Energy } from "@/lib/api";

const LABELS: Record<string, string> = {
  ALLSKY_SFC_SW_DWN: "Güneş ışınımı",
  WS10M: "Rüzgâr hızı",
  arazi_egimi_yuzde: "Arazi eğimi",
  tesvik_bolgesi: "Teşvik bölgesi",
  T2M: "Sıcaklık",
  RH2M: "Nem",
};

export function GlobalShapSummary({ energy }: { energy: Energy }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["global-shap", energy],
    queryFn: () => api.globalShap(energy),
  });

  if (isLoading) return <p className="muted">Global açıklama yükleniyor…</p>;
  if (error || !data) {
    return <p className="error-text">Global SHAP özeti alınamadı.</p>;
  }

  const top = data.feature_importance.slice(0, 5);
  const max = Math.max(...top.map((item) => item.mean_abs_shap), 1);

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <h2>Model genel açıklaması</h2>
          <p>
            {energy.toUpperCase()} modelinde skoru en çok etkileyen değişkenler.
          </p>
        </div>
        <span className="muted">{data.sample_size} örnek</span>
      </div>
      <div className="bar-list">
        {top.map((item) => (
          <div key={item.feature} className="bar-row">
            <span>{LABELS[item.feature] ?? item.feature}</span>
            <div className="bar-track">
              <div
                className={`bar-fill ${energy}`}
                style={{ width: `${(item.mean_abs_shap / max) * 100}%` }}
              />
            </div>
            <strong>{item.mean_abs_shap.toFixed(2)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
