// src/lib/api.ts
export async function getClientProfile() {
  return authFetch(`/client/me`);
}
export async function updateClientSettings(body: { optimize_for?: string; config_yaml?: string; }) {
  return authFetch(`/client/settings`, { method: "PUT", body: JSON.stringify(body) });
}
export async function updateClientBilling(body: { billing_email?: string; plan?: string; monthly_quota?: number; next_billing_date?: string; }) {
  return authFetch(`/client/billing`, { method: "PUT", body: JSON.stringify(body) });
}
export async function listClientModels() {
  return authFetch(`/client/models`);
}

export type ListParams = {
  userId?: string;
  q?: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
  page?: number;
  pageSize?: number;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "https://taulayer-api.onrender.com/api";

export async function authFetch(path: string, init: RequestInit = {}) {
  const { supabase } = await import("@/supabaseClient"); // dynamic import to avoid cycles
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string,string> ?? {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    // let caller see shape
    let body: any = {};
    try { body = await res.json(); } catch { /* ignore */ }
    const err = new Error(body?.error || res.statusText);
    (err as any).status = res.status;
    (err as any).body = body;
    throw err;
  }
  return res.json();
}

export async function listRequests(params: ListParams) {
  const q = new URLSearchParams();
  if (params.userId) q.set("user_id_like", params.userId);
  if (params.q) q.set("q", params.q);
  if (params.sortBy) q.set("sort_by", params.sortBy);
  if (params.sortDir) q.set("sort_dir", params.sortDir);
  if (params.page) q.set("page", String(params.page));
  if (params.pageSize) q.set("page_size", String(params.pageSize));
  return authFetch(`/requests?${q.toString()}`);
}

export async function getMetrics() {
  return authFetch(`/metrics`);
}
