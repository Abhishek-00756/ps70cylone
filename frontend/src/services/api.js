// All backend calls go through this module so no page ever invents data.
export const API_BASE_URL = window.CYCLONEAI_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch (_) {}
    const err = new Error(body?.error || `Request failed: ${res.status}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res.blob();
}

export const api = {
  health: () => request("/health"),
  systemStatus: () => request("/api/system/status"),
  dashboard: () => request("/api/dashboard"),
  cyclones: () => request("/api/cyclones"),
  cyclone: (id) => request(`/api/cyclones/${id}`),
  track: (id) => request(`/api/cyclones/${id}/track`),
  intensity: (id) => request(`/api/cyclones/${id}/intensity`),
  features: (id) => request(`/api/cyclones/${id}/features`),
  risk: (id) => request(`/api/cyclones/${id}/risk`),
  satelliteMeta: (id) => request(`/api/cyclones/${id}/satellite`),
  satelliteFrameUrl: (id, timestamp, channel) =>
    `${API_BASE_URL}/api/cyclones/${id}/satellite/frame?timestamp=${encodeURIComponent(timestamp)}&channel=${channel}`,
  alerts: () => request("/api/alerts"),
  modelMetrics: () => request("/api/model/metrics"),
  dataSources: () => request("/api/data-sources"),
  analyze: () => request("/api/analyze", { method: "POST" }),
  predict: (horizons) => request("/api/predict", { method: "POST", body: JSON.stringify({ horizons_hours: horizons }) }),
};

export function fmtTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch (_) {
    return iso;
  }
}

export function tagClass(level) {
  return (level || "").toString().toLowerCase();
}
