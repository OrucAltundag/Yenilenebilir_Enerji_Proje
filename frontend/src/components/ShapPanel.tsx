"use client";

import { useQuery } from "@tanstack/react-query";

import { api, type Energy } from "@/lib/api";

const LABELS: Record<string, string> = {
  ALLSKY_SFC_SW_DWN: "Güneş ışınımı",
  WS10M: "Rüzgâr hızı",
  tesvik_bolgesi: "Teşvik bölgesi",
  arazi_egimi_yuzde: "Arazi eğimi",
  T2M: "Sıcaklık",
  RH2M: "Nem",
  yuzey_alani_km2: "Yüzölçümü",
};

export function ShapPanel({ districtId, energy }: { districtId: string; energy: Energy }) {
  const { data, isLoading } = useQuery({
    queryKey: ["shap", districtId, energy],
    queryFn: () => api.districtShap(districtId, energy),
  });

  if (isLoading) return <p>SHAP hesaplanıyor…</p>;
  if (!data) return null;

  const top = data.contributions.slice(0, 6);
  const maxAbs = Math.max(...top.map((c) => Math.abs(c.shap_value)), 0.01);

  return (
    <div>
      <p style={{ fontSize: 13, opacity: 0.7 }}>
        Taban değer {data.expected_value.toFixed(1)} → tahmin{" "}
        {data.prediction_value.toFixed(1)} (model: {data.model_version})
      </p>
      {top.map((c) => {
        const pct = (Math.abs(c.shap_value) / maxAbs) * 100;
        const positive = c.shap_value >= 0;
        return (
          <div key={c.feature} style={{ marginBottom: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
              <span>{LABELS[c.feature] ?? c.feature}</span>
              <span style={{ color: positive ? "#91cf60" : "#fc8d59" }}>
                {positive ? "+" : ""}
                {c.shap_value.toFixed(2)}
              </span>
            </div>
            <div style={{ background: "#1c2740", borderRadius: 4, height: 8 }}>
              <div
                style={{
                  width: `${pct}%`,
                  height: 8,
                  borderRadius: 4,
                  background: positive ? "#91cf60" : "#fc8d59",
                }}
              />
            </div>
          </div>
        );
      })}
      <p style={{ fontSize: 11, opacity: 0.5, marginTop: 8 }}>
        SHAP nedensellik kanıtı değildir; model davranışını açıklar.
      </p>
    </div>
  );
}
