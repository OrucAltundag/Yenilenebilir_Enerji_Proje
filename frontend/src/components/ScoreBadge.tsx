export function scoreBand(score: number): { label: string; color: string } {
  if (score >= 80) return { label: "Çok Yüksek", color: "#1a9850" };
  if (score >= 60) return { label: "Yüksek", color: "#91cf60" };
  if (score >= 40) return { label: "Orta", color: "#fee08b" };
  if (score >= 20) return { label: "Düşük", color: "#fc8d59" };
  return { label: "Çok Düşük", color: "#d73027" };
}

export function ScoreBadge({ score }: { score: number }) {
  const band = scoreBand(score);
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 12,
        background: band.color,
        color: "#0b1220",
        fontWeight: 700,
        fontSize: 13,
      }}
      title={band.label}
    >
      {score.toFixed(1)}
    </span>
  );
}
