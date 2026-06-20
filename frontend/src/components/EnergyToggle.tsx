"use client";

import type { Energy } from "@/lib/api";

export function EnergyToggle({
  value,
  onChange,
}: {
  value: Energy;
  onChange: (e: Energy) => void;
}) {
  return (
    <div style={{ display: "inline-flex", gap: 4, background: "var(--color-surface)", padding: 4, borderRadius: 8 }}>
      {(["ges", "res"] as Energy[]).map((e) => (
        <button
          key={e}
          onClick={() => onChange(e)}
          style={{
            padding: "6px 16px",
            border: "none",
            borderRadius: 6,
            cursor: "pointer",
            fontWeight: 600,
            color: value === e ? "#0b1220" : "var(--color-text)",
            background:
              value === e
                ? e === "ges"
                  ? "var(--color-accent-ges)"
                  : "var(--color-accent-res)"
                : "transparent",
          }}
        >
          {e === "ges" ? "☀️ GES (Güneş)" : "🌬️ RES (Rüzgâr)"}
        </button>
      ))}
    </div>
  );
}
