"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function SystemStatus() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["readyz"],
    queryFn: api.readyz,
    refetchInterval: 30_000,
  });

  if (isLoading) return <div className="status-pill">Sistem kontrol ediliyor…</div>;
  if (error || !data) {
    return <div className="status-pill danger">API bağlantısı yok</div>;
  }

  return (
    <div className={`status-pill ${data.ready ? "ok" : "danger"}`}>
      {data.ready ? "Sistem hazır" : "Sistem eksik"} ·{" "}
      {data.detail.district_count ?? "—"} ilçe · v{data.version}
    </div>
  );
}
