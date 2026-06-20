"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import { AuthPanel } from "@/components/AuthPanel";
import { DistrictSearch } from "@/components/DistrictSearch";
import { EnergyToggle } from "@/components/EnergyToggle";
import { GlobalShapSummary } from "@/components/GlobalShapSummary";
import { RankingTable } from "@/components/RankingTable";
import { SystemStatus } from "@/components/SystemStatus";
import type { Energy } from "@/lib/api";

const DistrictMap = dynamic(
  () => import("@/components/DistrictMap").then((module) => module.DistrictMap),
  {
    ssr: false,
    loading: () => <p>Harita hazırlanıyor…</p>,
  }
);

export default function HomePage() {
  const [energy, setEnergy] = useState<Energy>("ges");

  return (
    <main style={{ maxWidth: 1180, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <header className="hero-header">
        <div>
          <h1 style={{ margin: 0 }}>Buraki</h1>
          <p style={{ opacity: 0.7, marginTop: 4 }}>
            Yapay Zekâ Destekli Yenilenebilir Enerji Yatırım Karar Destek Sistemi
          </p>
        </div>
        <SystemStatus />
      </header>

      <AuthPanel />

      <section style={{ marginBottom: 20 }}>
        <DistrictSearch />
      </section>

      <section
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
          flexWrap: "wrap",
          marginBottom: 16,
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 20 }}>Türkiye İlçe Skor Haritası</h2>
          <p style={{ margin: "4px 0 0", opacity: 0.65, fontSize: 13 }}>
            İlçeye tıklayarak ayrıntılı skor ve açıklamaları açın.
          </p>
        </div>
        <EnergyToggle value={energy} onChange={setEnergy} />
      </section>

      <DistrictMap energy={energy} />

      <section className="dashboard-grid">
        <div className="panel">
          <h2 style={{ margin: "0 0 12px", fontSize: 18 }}>
            Yıllık Ortalama Sıralama (2023)
          </h2>
          <RankingTable energy={energy} />
        </div>
        <GlobalShapSummary energy={energy} />
      </section>

      <footer style={{ marginTop: 32, fontSize: 12, opacity: 0.6 }}>
        Skorlar yatırım tavsiyesi değildir; ön eleme ve karşılaştırma amaçlıdır.
        Metodoloji sürümü 2023.1.
      </footer>
    </main>
  );
}
