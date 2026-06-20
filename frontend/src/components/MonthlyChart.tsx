"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MonthlyPoint } from "@/lib/api";

const AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];

export function MonthlyChart({ data }: { data: MonthlyPoint[] }) {
  const chart = data.map((d) => ({
    ay: AYLAR[d.ay - 1] ?? d.ay,
    GES: d.ges_mean,
    RES: d.res_mean,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={chart}>
        <XAxis dataKey="ay" stroke="#889" fontSize={12} />
        <YAxis domain={[0, 100]} stroke="#889" fontSize={12} />
        <Tooltip
          contentStyle={{ background: "#131a2c", border: "1px solid #233" }}
        />
        <Line type="monotone" dataKey="GES" stroke="#f5b400" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="RES" stroke="#4cc3ff" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
