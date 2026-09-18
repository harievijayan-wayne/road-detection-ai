const API_BASE = "http://localhost:8000/api";

export async function fetchOverviewAnalytics() {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) throw new Error("Failed to fetch analytics");
  return res.json();
}

export async function fetchMapTelemetry() {
  const res = await fetch(`${API_BASE}/map`);
  if (!res.ok) throw new Error("Failed to fetch map data");
  return res.json();
}

export async function fetchInspections() {
  const res = await fetch(`${API_BASE}/inspections`);
  if (!res.ok) throw new Error("Failed to fetch inspections");
  return res.json();
}

export async function fetchDamages(params = {}) {
  const url = new URL(`${API_BASE}/damages`);
  Object.keys(params).forEach(key => {
    if (params[key]) url.searchParams.append(key, params[key]);
  });
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch damage events");
  return res.json();
}

export async function fetchDamageDetail(id) {
  const res = await fetch(`${API_BASE}/damages/${id}`);
  if (!res.ok) throw new Error("Failed to fetch damage detail");
  return res.json();
}

export async function reviewDamageEvent(id, data) {
  const res = await fetch(`${API_BASE}/damages/${id}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to review event");
  return res.json();
}

export async function detectImageUpload(formData) {
  const res = await fetch(`${API_BASE}/detect/image`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Image detection failed");
  }
  return res.json();
}

export async function detectVideoUpload(formData) {
  const res = await fetch(`${API_BASE}/detect/video`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Video detection failed" }));
    throw new Error(err.detail || "Video detection failed");
  }
  return res.json();
}

export async function fetchDemoSamples() {
  const res = await fetch(`${API_BASE}/demo-samples`);
  if (!res.ok) throw new Error("Failed to fetch demo samples");
  return res.json();
}

export async function generateReport(payload) {
  const res = await fetch(`${API_BASE}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to generate report");
  return res.json();
}

export function getMediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  if (path.startsWith("/api")) return `http://localhost:8000${path}`;
  return `http://localhost:8000/api/uploads/${path.split(/[\\/]/).pop()}`;
}
