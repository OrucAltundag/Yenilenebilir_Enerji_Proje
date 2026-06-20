import type { FeatureCollection, MultiPolygon, Polygon } from "geojson";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "buraki_access_token";
const ROLE_KEY = "buraki_role";
const USER_KEY = "buraki_username";

export type Energy = "ges" | "res";

export type DistrictItem = {
  district_id: string;
  province: string;
  district: string;
};

export type ScoreMapItem = DistrictItem & {
  score: number;
  percentile?: number;
};

export type DistrictGeometryProperties = DistrictItem & {
  shape_id: string;
  shape_name: string;
  match_method: string;
};

export type DistrictFeatureCollection = FeatureCollection<
  Polygon | MultiPolygon,
  DistrictGeometryProperties
>;

export type MonthlyPoint = { ay: number; ges_mean: number; res_mean: number };

export type DistrictSummary = DistrictItem & {
  year: number;
  ges_score_mean: number;
  res_score_mean: number;
  national_rank_ges: number;
  national_rank_res: number;
  percentile_ges: number;
  percentile_res: number;
  features: Record<string, number>;
  monthly: MonthlyPoint[];
  data_version: string;
  scoring_version: string;
};

export type ShapContribution = {
  feature: string;
  value: number;
  shap_value: number;
};

export type ShapExplanation = {
  energy: Energy;
  expected_value: number;
  prediction_value: number;
  contributions: ShapContribution[];
  model_version: string;
};

export type ScenarioResult = {
  district_id: string;
  baseline_ges: number;
  baseline_res: number;
  scenario_ges: number;
  scenario_res: number;
  delta_ges: number;
  delta_res: number;
  scoring_version: string;
};

export type AuthSession = {
  username: string;
  role: string;
  access_token: string;
};

export type Project = {
  id: number;
  owner_id: string;
  name: string;
  note: string | null;
  district_ids: string[];
  energy: Energy;
  created_at: string;
};

export type SavedScenario = {
  id: number;
  owner_id: string;
  project_id: number | null;
  district_id: string;
  overrides: Record<string, number>;
  input_snapshot: Record<string, number>;
  result: {
    baseline: { ges: number; res: number };
    scenario: { ges: number; res: number };
    delta_ges: number;
    delta_res: number;
  };
  scoring_version: string;
  created_at: string;
};

export type ActiveDataset = { active: string | null; status?: string };
export type AuditEntry = {
  actor: string;
  action: string;
  detail: Record<string, unknown>;
  created_at: string;
};

export type Readyz = {
  ready: boolean;
  checks: Record<string, boolean>;
  detail: {
    district_count?: number;
    district_geometry_bytes?: number;
    data_error?: string;
    model_error?: string;
  };
  version: string;
};

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function notifyAuthChange() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("buraki-auth-change"));
  }
}

export function getStoredSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const access_token = window.localStorage.getItem(TOKEN_KEY);
  const role = window.localStorage.getItem(ROLE_KEY);
  const username = window.localStorage.getItem(USER_KEY);
  if (!access_token || !role || !username) return null;
  return { access_token, role, username };
}

export function storeSession(session: AuthSession) {
  window.localStorage.setItem(TOKEN_KEY, session.access_token);
  window.localStorage.setItem(ROLE_KEY, session.role);
  window.localStorage.setItem(USER_KEY, session.username);
  notifyAuthChange();
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(ROLE_KEY);
  window.localStorage.removeItem(USER_KEY);
  notifyAuthChange();
}

async function parseError(res: Response, path: string): Promise<Error> {
  try {
    const body = await res.json();
    const detail =
      typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    return new Error(`API hatası ${res.status}: ${detail || path}`);
  } catch {
    return new Error(`API hatası ${res.status}: ${path}`);
  }
}

async function getJSON<T>(path: string, authenticated = false): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { Accept: "application/json", ...(authenticated ? authHeaders() : {}) },
  });
  if (!res.ok) throw await parseError(res, path);
  return res.json();
}

async function postJSON<T>(
  path: string,
  body: unknown,
  authenticated = false
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(authenticated ? authHeaders() : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await parseError(res, path);
  return res.json();
}

async function deleteRequest(path: string, authenticated = false): Promise<void> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: { ...(authenticated ? authHeaders() : {}) },
  });
  if (!res.ok) throw await parseError(res, path);
}

export const api = {
  readyz: () => getJSON<Readyz>(`/readyz`),
  login: async (username: string, password: string) => {
    const token = await postJSON<{ access_token: string; role: string }>(
      `/auth/login`,
      { username, password }
    );
    const session = { ...token, username };
    storeSession(session);
    return session;
  },
  search: (q: string, limit = 10) =>
    getJSON<{ items: DistrictItem[]; total: number }>(
      `/districts/search?q=${encodeURIComponent(q)}&limit=${limit}`
    ),
  summary: (id: string) => getJSON<DistrictSummary>(`/districts/${id}/summary`),
  districtGeoJSON: () =>
    getJSON<DistrictFeatureCollection>(`/districts/geojson`),
  ranking: (energy: Energy, limit = 20) =>
    getJSON<{ energy: Energy; year: number; items: ScoreMapItem[] }>(
      `/scores/ranking?energy=${energy}&limit=${limit}`
    ),
  scoreMap: (energy: Energy) =>
    getJSON<{ energy: Energy; items: ScoreMapItem[] }>(
      `/scores/map?energy=${energy}`
    ),
  districtShap: (id: string, energy: Energy) =>
    getJSON<ShapExplanation>(`/shap/district/${id}/${energy}`),
  globalShap: (energy: Energy) =>
    getJSON<{
      energy: Energy;
      sample_size: number;
      expected_value: number;
      feature_importance: { feature: string; mean_abs_shap: number }[];
    }>(`/shap/global/${energy}`),
  simulate: (district_id: string, overrides: Record<string, number>) =>
    postJSON<ScenarioResult>(`/scenarios/simulate`, { district_id, overrides }),
  createProject: (payload: {
    name: string;
    note?: string | null;
    district_ids: string[];
    energy: Energy;
  }) => postJSON<Project>(`/projects`, payload, true),
  listProjects: () => getJSON<Project[]>(`/projects`, true),
  deleteProject: (id: number) => deleteRequest(`/projects/${id}`, true),
  saveScenario: (payload: {
    district_id: string;
    overrides: Record<string, number>;
    project_id?: number | null;
  }) => postJSON<SavedScenario>(`/projects/scenarios`, payload, true),
  listScenarios: () => getJSON<SavedScenario[]>(`/projects/scenarios/list`, true),
  reportUrl: (districtId: string, energy: Energy) =>
    `${BASE_URL}/reports/district/${districtId}.pdf?energy=${energy}`,
  downloadReport: async (districtId: string, energy: Energy) => {
    const res = await fetch(api.reportUrl(districtId, energy), {
      headers: authHeaders(),
    });
    if (!res.ok) throw await parseError(res, `/reports/district/${districtId}.pdf`);
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = /filename="([^"]+)"/.exec(disposition);
    return { blob, filename: match?.[1] ?? `buraki-${districtId}-${energy}.pdf` };
  },
  activeDataset: () => getJSON<ActiveDataset>(`/admin/dataset/active`, true),
  publishDataset: (version: string, district_count = 957, area_zero = 0) =>
    postJSON<{ active: string; status: string }>(
      `/admin/dataset/publish`,
      { version, district_count, area_zero },
      true
    ),
  rollbackDataset: (version: string) =>
    postJSON<{ active: string }>(
      `/admin/dataset/rollback?version=${encodeURIComponent(version)}`,
      {},
      true
    ),
  auditLog: (limit = 20) => getJSON<AuditEntry[]>(`/admin/audit?limit=${limit}`, true),
};
