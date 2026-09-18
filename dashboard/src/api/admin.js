const API_BASE = "http://localhost:8000";

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error("Giriş başarısız");
  return response.json();
}

export async function getBlacklist(token) {
  const response = await fetch(`${API_BASE}/admin/blacklist`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

export async function unbanIp(token, ip) {
  const response = await fetch(`${API_BASE}/admin/blacklist/${ip}/unban`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

export async function getRules(token) {
  const response = await fetch(`${API_BASE}/admin/rules`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

export async function createRule(token, rule) {
  const params = new URLSearchParams(rule).toString();
  const response = await fetch(`${API_BASE}/admin/rules?${params}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

export async function getAuditLog(token) {
  const response = await fetch(`${API_BASE}/admin/audit-log`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

export async function getReportSummary(token, days = 7) {
  const response = await fetch(`${API_BASE}/admin/reports/summary?days=${days}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}
