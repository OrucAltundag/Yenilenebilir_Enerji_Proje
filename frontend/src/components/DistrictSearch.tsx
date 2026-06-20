"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function DistrictSearch() {
  const [q, setQ] = useState("");
  const { data } = useQuery({
    queryKey: ["search", q],
    queryFn: () => api.search(q, 8),
    enabled: q.trim().length >= 2,
  });

  return (
    <div style={{ position: "relative" }}>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="İl veya ilçe ara…"
        aria-label="İlçe arama"
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: 8,
          border: "1px solid #233",
          background: "var(--color-surface)",
          color: "var(--color-text)",
        }}
      />
      {data && data.items.length > 0 && (
        <ul
          style={{
            listStyle: "none",
            margin: "4px 0 0",
            padding: 4,
            position: "absolute",
            width: "100%",
            background: "var(--color-surface)",
            borderRadius: 8,
            border: "1px solid #233",
            zIndex: 10,
          }}
        >
          {data.items.map((it) => (
            <li key={it.district_id}>
              <Link
                href={`/district/${it.district_id}`}
                style={{
                  display: "block",
                  padding: "8px 10px",
                  color: "var(--color-text)",
                  textDecoration: "none",
                }}
              >
                {it.province} / {it.district}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
