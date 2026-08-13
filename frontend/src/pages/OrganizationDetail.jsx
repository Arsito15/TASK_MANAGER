import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";

import Layout from "../components/Layout.jsx";
import Spinner from "../components/Spinner.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";

import { useAuth } from "../context/AuthContext.jsx";
import {
  getOrganization,
  getMembers,
  addMember,
  updateMemberRole,
  removeMember,
} from "../api/organizations";
import { getProjects, createProject } from "../api/projects";

const ROLES = ["OWNER", "ADMIN", "MEMBER", "VIEWER"];

export default function OrganizationDetail({ params }) {
  const { slug } = params;
  const { user } = useAuth();
  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showMemberForm, setShowMemberForm] = useState(false);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [newMember, setNewMember] = useState({ email: "", role: "MEMBER" });
  const [newProject, setNewProject] = useState({ name: "", description: "" });
  const [confirmRemove, setConfirmRemove] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const myRole = org?.my_role;
  const canManage = myRole === "OWNER" || myRole === "ADMIN";

  const load = useCallback(async () => {
    try {
      const [orgData, membersData, projectsData] = await Promise.all([
        getOrganization(slug),
        getMembers(slug),
        getProjects(slug),
      ]);
      setOrg(orgData);
      setMembers(membersData.results || membersData);
      setProjects(projectsData.results || projectsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const m = await addMember(slug, newMember.email, newMember.role);
      setMembers([...members, m]);
      setNewMember({ email: "", role: "MEMBER" });
      setShowMemberForm(false);
    } catch (err) {
      setError(err.data?.user_email || err.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRoleChange = async (memberId, role) => {
    try {
      const m = await updateMemberRole(slug, memberId, role);
      setMembers(members.map((x) => (x.id === memberId ? m : x)));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRemoveMember = async () => {
    if (!confirmRemove) return;
    try {
      await removeMember(slug, confirmRemove.id);
      setMembers(members.filter((x) => x.id !== confirmRemove.id));
    } catch (err) {
      setError(err.message);
    }
    setConfirmRemove(null);
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const p = await createProject(slug, newProject);
      setProjects([...projects, p]);
      setNewProject({ name: "", description: "" });
      setShowProjectForm(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <Spinner />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="page-header">
        <div>
          <Link to="/" style={{ fontSize: "0.8rem", color: "var(--color-text-muted)" }}>
            &larr; Organizations
          </Link>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 600, fontFamily: "var(--font-serif)", letterSpacing: "-0.02em", marginTop: "0.25rem" }}>
            {org?.name}
          </h1>
        </div>
        {canManage && (
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button className="btn-secondary" onClick={() => setShowMemberForm(!showMemberForm)}>
              Add Member
            </button>
            <button className="btn-primary" onClick={() => setShowProjectForm(!showProjectForm)}>
              + New Project
            </button>
          </div>
        )}
      </div>

      <ErrorBanner error={error} />

      {showMemberForm && (
        <form onSubmit={handleAddMember} className="card" style={{ marginBottom: "1.5rem" }}>
          <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "1rem" }}>Add Member</div>
          <div className="form-group">
            <label>User Email</label>
            <input
              type="email"
              value={newMember.email}
              onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
              placeholder="colleague@example.com"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Role</label>
            <select
              value={newMember.role}
              onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Adding…" : "Add Member"}
          </button>
        </form>
      )}

      {showProjectForm && (
        <form onSubmit={handleCreateProject} className="card" style={{ marginBottom: "1.5rem" }}>
          <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "1rem" }}>New Project</div>
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={newProject.name}
              onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
              placeholder="e.g. Website Redesign"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={newProject.description}
              onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
              rows={3}
              placeholder="Brief description (optional)"
            />
          </div>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Creating…" : "Create Project"}
          </button>
        </form>
      )}

      <div style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "0.8rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--color-text-muted)", marginBottom: "0.75rem" }}>
          Members
        </h2>
        {members.length === 0 ? (
          <EmptyState message="No members." />
        ) : (
          <div style={{ display: "grid", gap: "0.4rem" }}>
            {members.map((m) => (
              <div
                key={m.id}
                className="card"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.75rem 1.25rem",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{m.user}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "0.15rem" }}>
                    Joined {new Date(m.joined_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  {canManage && m.user !== user.email ? (
                    <>
                      <select
                        value={m.role}
                        onChange={(e) => handleRoleChange(m.id, e.target.value)}
                        style={{ width: "auto", fontSize: "0.8rem", padding: "0.3rem 1.5rem 0.3rem 0.5rem" }}
                        disabled={m.role === "OWNER"}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                      {m.role !== "OWNER" && (
                        <button
                          className="btn-danger"
                          onClick={() => setConfirmRemove(m)}
                          style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
                        >
                          Remove
                        </button>
                      )}
                    </>
                  ) : (
                    <span className={`badge badge-${m.role}`}>{m.role}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 style={{ fontSize: "0.8rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--color-text-muted)", marginBottom: "0.75rem" }}>
          Projects
        </h2>
        {projects.length === 0 ? (
          <EmptyState message="No projects yet." />
        ) : (
          <div style={{ display: "grid", gap: "0.4rem" }}>
            {projects.map((p) => (
              <Link
                key={p.id}
                to={`/projects/${p.id}`}
                className="card card-hover"
                style={{
                  textDecoration: "none",
                  color: "inherit",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.75rem 1.25rem",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{p.name}</div>
                  {p.description && (
                    <div style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", marginTop: "0.15rem" }}>
                      {p.description}
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  <span className={`badge badge-${p.status}`}>{p.status}</span>
                  <span style={{ color: "var(--color-text-muted)" }}>&rarr;</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {confirmRemove && (
        <ConfirmDialog
          message={`Remove ${confirmRemove.user} from this organization?`}
          onConfirm={handleRemoveMember}
          onCancel={() => setConfirmRemove(null)}
        />
      )}
    </Layout>
  );
}