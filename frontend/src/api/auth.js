import { apiCall, setTokens, clearTokens, API_URL } from "./client";

export async function register(username, email, password) {
  const data = await apiCall("/auth/register/", {
    method: "POST",
    body: JSON.stringify({
      username,
      email,
      password,
      password2: password,
    }),
  });
  return data;
}

export async function login(email, password) {
  const resp = await fetch(`${API_URL}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await resp.json();
  if (!resp.ok) {
    const error = new Error(data.detail || "Login failed");
    error.data = data;
    error.status = resp.status;
    throw error;
  }
  setTokens(data.access, data.refresh);
  return data;
}

export async function logout() {
  const { refresh } = JSON.parse(
    '{"refresh":"' + localStorage.getItem("refresh_token") + '"}'
  );
  try {
    await apiCall("/auth/logout/", {
      method: "POST",
      body: JSON.stringify({ refresh: localStorage.getItem("refresh_token") }),
    });
  } catch {
  }
  clearTokens();
}

export async function getMe() {
  return apiCall("/auth/me/");
}