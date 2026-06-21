"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DeveloperShell } from "@/components/DeveloperShell";
import { api } from "@/lib/api";

export default function ModelComparePage() {
  const [left, setLeft] = useState(0); const [right, setRight] = useState(0);
  const models = useQuery({ queryKey: ["compare-models"], queryFn: () => api.models({ limit: 200 }) });
  const comparison = useQuery({ queryKey: ["model-comparison", left, right], queryFn: () => api.compareModels(left, right), enabled: left > 0 && right > 0 && left !== right });
  return <DeveloperShell title="Model karşılaştırma" description="İki model sürümünün metrik ve özellik önem farklarını görün."><section className="panel"><div className="compare-selectors">{[[left,setLeft,"Model A"],[right,setRight,"Model B"]].map(([value,setter,label]) => <label className="field-stack" key={String(label)}><span>{String(label)}</span><select value={Number(value)} onChange={(event) => (setter as (id:number)=>void)(Number(event.target.value))}><option value={0}>Seçin</option>{models.data?.map((model) => <option key={model.id} value={model.id}>#{model.id} · {model.energy_type.toUpperCase()} · {model.model_version}</option>)}</select></label>)}</div>{comparison.data && <div className="grid-2"><pre className="mini-json">{JSON.stringify(comparison.data.metric_diff, null, 2)}</pre><pre className="mini-json">{JSON.stringify(comparison.data.feature_importance_diff, null, 2)}</pre></div>}{comparison.error && <p className="error-text">{(comparison.error as Error).message}</p>}</section></DeveloperShell>;
}
