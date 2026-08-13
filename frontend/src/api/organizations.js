import { apiCall } from "./client";

export async function getMyOrganizations() {
  return apiCall("/organizations/");
}

export async function getOrganization(slug) {
  return apiCall(`/organizations/${slug}/`);
}

export async function createOrganization(name) {
  return apiCall("/organizations/", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function updateOrganization(slug, data) {
  return apiCall(`/organizations/${slug}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getMembers(slug) {
  return apiCall(`/organizations/${slug}/members/`);
}

export async function addMember(slug, email, role) {
  return apiCall(`/organizations/${slug}/members/`, {
    method: "POST",
    body: JSON.stringify({ user_email: email, role }),
  });
}

export async function updateMemberRole(slug, memberId, role) {
  return apiCall(`/organizations/${slug}/members/${memberId}/`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export async function removeMember(slug, memberId) {
  return apiCall(`/organizations/${slug}/members/${memberId}/`, {
    method: "DELETE",
  });
}