"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { api, type Energy } from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";

export function RankingTable({ energy }: { energy: Energy }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["ranking", energy],
    queryFn: () => api.ranking(energy, 20),
  });

  if (isLoading) return <p>Yükleniyor…</p>;
  if (error) return <p style={{ color: "#fc8d59" }}>Hata: {(error as Error).message}</p>;

  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
      <thead>
        <tr style={{ textAlign: "left", opacity: 0.7 }}>
          <th style={{ padding: 8 }}>#</th>
          <th style={{ padding: 8 }}>İl / İlçe</th>
          <th style={{ padding: 8 }}>Skor</th>
          <th style={{ padding: 8 }}>Yüzdelik</th>
        </tr>
      </thead>
      <tbody>
        {data?.items.map((it, i) => (
          <tr key={it.district_id} style={{ borderTop: "1px solid #233" }}>
            <td style={{ padding: 8, opacity: 0.6 }}>{i + 1}</td>
            <td style={{ padding: 8 }}>
              <Link href={`/district/${it.district_id}`} style={{ color: "var(--color-text)" }}>
                {it.province} / {it.district}
              </Link>
            </td>
            <td style={{ padding: 8 }}>
              <ScoreBadge score={it.score} />
            </td>
            <td style={{ padding: 8, opacity: 0.7 }}>
              {it.percentile ? `%${it.percentile.toFixed(0)}` : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
