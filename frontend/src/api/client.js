const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

let refreshPromise = null;

function getTokens() {
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

function setTokens(access, refresh) {
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshToken() {
  const { refresh } = getTokens();
  if (!refresh) {
    clearTokens();
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    })
      .then((resp) => {
        if (!resp.ok) throw new Error("Refresh failed");
        return resp.json();
      })
      .then((data) => {
        setTokens(data.access, data.refresh);
        return data.access;
      })
      .catch(() => {
        clearTokens();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

export async function apiRequest(endpoint, options = {}) {
  const { access } = getTokens();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (access) {
    headers["Authorization"] = `Bearer ${access}`;
  }

  let resp = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (resp.status === 401 && access) {
    const newToken = await refreshToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      resp = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
      });
    }
  }

  return resp;
}

export async function apiCall(endpoint, options = {}) {
  const resp = await apiRequest(endpoint, options);
  const data = resp.status !== 204 ? await resp.json().catch(() => null) : null;

  if (!resp.ok) {
    const error = new Error(
      (data && (data.detail || JSON.stringify(data))) || `HTTP ${resp.status}`
    );
    error.status = resp.status;
    error.data = data;
    throw error;
  }

  return data;
}

export { setTokens, clearTokens, getTokens, API_URL };