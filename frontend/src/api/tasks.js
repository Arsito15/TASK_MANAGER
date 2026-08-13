import { apiCall } from "./client";

export async function getTasks(projectId, params = {}) {
  let url = `/projects/${projectId}/tasks/`;
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.priority) qs.set("priority", params.priority);
  if (params.assignee) qs.set("assignee", params.assignee);
  if (params.search) qs.set("search", params.search);
  if (params.page) qs.set("page", params.page);
  const qsStr = qs.toString();
  if (qsStr) url += `?${qsStr}`;
  return apiCall(url);
}

export async function getTask(id) {
  return apiCall(`/tasks/${id}/`);
}

export async function createTask(projectId, data) {
  return apiCall(`/projects/${projectId}/tasks/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTask(projectId, id, data) {
  return apiCall(`/projects/${projectId}/tasks/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteTask(projectId, id) {
  return apiCall(`/projects/${projectId}/tasks/${id}/`, {
    method: "DELETE",
  });
}

export async function changeTaskStatus(projectId, id, status) {
  return apiCall(`/projects/${projectId}/tasks/${id}/change-status/`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}