import { apiCall } from "./client";

export async function getProjects(orgSlug, params = {}) {
  let url = `/organizations/${orgSlug}/projects/`;
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.page) qs.set("page", params.page);
  const qsStr = qs.toString();
  if (qsStr) url += `?${qsStr}`;
  return apiCall(url);
}

export async function getProject(id) {
  return apiCall(`/projects/${id}/`);
}

export async function createProject(orgSlug, data) {
  return apiCall(`/organizations/${orgSlug}/projects/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateProject(id, data) {
  return apiCall(`/projects/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id) {
  return apiCall(`/projects/${id}/`, { method: "DELETE" });
}

export async function getProjectSummary(id) {
  return apiCall(`/projects/${id}/summary/`);
}