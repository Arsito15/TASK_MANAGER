import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";

import Layout from "../components/Layout.jsx";
import Spinner from "../components/Spinner.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import Pagination from "../components/Pagination.jsx";

import { useAuth } from "../context/AuthContext.jsx";
import { getProject, getProjectSummary } from "../api/projects";
import { getMembers } from "../api/organizations";
import {
  getTasks,
  createTask,
  updateTask,
  deleteTask,
  changeTaskStatus,
} from "../api/tasks";

const STATUS_OPTIONS = ["TODO", "IN_PROGRESS", "DONE"];
const PRIORITY_OPTIONS = ["LOW", "MEDIUM", "HIGH"];
const STATUS_DOT = { TODO: "#a3a3a3", IN_PROGRESS: "#f59e0b", DONE: "#16a34a" };

export default function ProjectDetail({ params }) {
  const { id } = params;
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [orgSlug, setOrgSlug] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [count, setCount] = useState(0);
  const [next, setNext] = useState(null);
  const [previous, setPrevious] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [filters, setFilters] = useState({ status: "", priority: "", search: "" });
  const [summary, setSummary] = useState(null);
  const [members, setMembers] = useState([]);
  const [taskForm, setTaskForm] = useState({
    title: "",
    description: "",
    status: "TODO",
    priority: "MEDIUM",
    assignee: "",
    due_date: "",
  });

  const myRole = project?.my_role;
  const canCreate = myRole && myRole !== "VIEWER";
  const canManage = (task) => {
    if (!myRole) return false;
    if (myRole === "OWNER" || myRole === "ADMIN") return true;
    if (myRole === "MEMBER") return task.created_by === user?.id;
    return false;
  };

  const loadProject = useCallback(async () => {
    try {
      const p = await getProject(id);
      setProject(p);
      setOrgSlug(p.organization_slug);
    } catch (err) {
      setError(err.message);
    }
  }, [id]);

  const loadTasks = useCallback(async () => {
    try {
      const params = { page };
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.search) params.search = filters.search;
      const data = await getTasks(id, params);
      setTasks(data.results || []);
      setCount(data.count || 0);
      setNext(data.next);
      setPrevious(data.previous);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id, page, filters]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const loadSummary = useCallback(async () => {
    try {
      const data = await getProjectSummary(id);
      setSummary(data.counts);
    } catch {
      // Non-critical, silent fail
    }
  }, [id]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    if (orgSlug) {
      getMembers(orgSlug)
        .then((data) => setMembers(data.results || data))
        .catch(() => {});
    }
  }, [orgSlug]);

  const handleSubmitTask = async (e) => {
    e.preventDefault();
    setError(null);
    const payload = { ...taskForm };
    if (!payload.assignee) delete payload.assignee;
    if (!payload.due_date) delete payload.due_date;

    try {
      if (editingTask) {
        const updated = await updateTask(id, editingTask.id, payload);
        setTasks(tasks.map((t) => (t.id === editingTask.id ? updated : t)));
      } else {
        const created = await createTask(id, payload);
        setTasks([created, ...tasks]);
      }
      setTaskForm({
        title: "",
        description: "",
        status: "TODO",
        priority: "MEDIUM",
        assignee: "",
        due_date: "",
      });
      setEditingTask(null);
      setShowForm(false);
      loadSummary();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await deleteTask(id, confirmDelete.id);
      setTasks(tasks.filter((t) => t.id !== confirmDelete.id));
      loadSummary();
    } catch (err) {
      setError(err.message);
    }
    setConfirmDelete(null);
  };

  const handleStatusChange = async (taskId, newStatus) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
    );
    try {
      await changeTaskStatus(id, taskId, newStatus);
      loadSummary();
    } catch (err) {
      setError(err.message);
      loadTasks();
    }
  };

  const handleEdit = (task) => {
    setEditingTask(task);
    setTaskForm({
      title: task.title,
      description: task.description,
      status: task.status,
      priority: task.priority,
      assignee: task.assignee || "",
      due_date: task.due_date || "",
    });
    setShowForm(true);
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
    setPage(1);
  };

  return (
    <Layout>
      <div className="page-header">
        <div>
          <Link to={project ? `/orgs/${orgSlug}` : "/"} style={{ display: "block", fontSize: "0.8rem", color: "var(--color-text-muted)" }}>
            &larr; Back to organization
          </Link>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 600, fontFamily: "var(--font-serif)", letterSpacing: "-0.02em", marginTop: "0.25rem" }}>
            {project?.name || "Project"}
          </h1>
          {summary && (
            <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.6rem", flexWrap: "wrap" }}>
              {STATUS_OPTIONS.map((s) => (
                <span key={s} className="summary-badge">
                  <span className="summary-dot" style={{ background: STATUS_DOT[s] }} />
                  {s.replace("_", " ")}: {summary[s] || 0}
                </span>
              ))}
              <span className="summary-badge" style={{ fontWeight: 600 }}>
                Total: {summary.total || 0}
              </span>
            </div>
          )}
        </div>
        {canCreate && (
          <button className="btn-primary" onClick={() => { setEditingTask(null); setShowForm(!showForm); }}>
            {showForm ? "Cancel" : "+ New Task"}
          </button>
        )}
      </div>

      <ErrorBanner error={error} />

      {showForm && (
        <form onSubmit={handleSubmitTask} className="card" style={{ marginBottom: "1.5rem" }}>
          <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "1rem" }}>
            {editingTask ? "Edit Task" : "New Task"}
          </div>
          <div className="form-group">
            <label>Title</label>
            <input
              type="text"
              value={taskForm.title}
              onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
              placeholder="e.g. Fix login page bug"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={taskForm.description}
              onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
              rows={3}
              placeholder="Optional details…"
            />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label>Status</label>
              <select
                value={taskForm.status}
                onChange={(e) => setTaskForm({ ...taskForm, status: e.target.value })}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s.replace("_", " ")}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select
                value={taskForm.priority}
                onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label>Assignee (optional)</label>
              <select
                value={taskForm.assignee}
                onChange={(e) => setTaskForm({ ...taskForm, assignee: e.target.value })}
              >
                <option value="">Unassigned</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.username || m.user} ({m.role})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Due Date (optional)</label>
              <input
                type="date"
                value={taskForm.due_date}
                onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
              />
            </div>
          </div>
          <button type="submit" className="btn-primary">
            {editingTask ? "Update Task" : "Create Task"}
          </button>
        </form>
      )}

      <div className="card" style={{ marginBottom: "1rem", display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "flex-end" }}>
        <div className="form-group" style={{ marginBottom: 0, minWidth: 140 }}>
          <label>Status</label>
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange("status", e.target.value)}
          >
            <option value="">All</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s.replace("_", " ")}</option>
            ))}
          </select>
        </div>
        <div className="form-group" style={{ marginBottom: 0, minWidth: 140 }}>
          <label>Priority</label>
          <select
            value={filters.priority}
            onChange={(e) => handleFilterChange("priority", e.target.value)}
          >
            <option value="">All</option>
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: 180 }}>
          <label>Search</label>
          <input
            type="text"
            value={filters.search}
            onChange={(e) => handleFilterChange("search", e.target.value)}
            placeholder="Search by title…"
          />
        </div>
      </div>

      {loading ? (
        <Spinner />
      ) : tasks.length === 0 ? (
        <EmptyState message="No tasks found. Create one to get started!" />
      ) : (
        <>
          <div style={{ display: "grid", gap: "0.4rem" }}>
            {tasks.map((task) => (
              <div key={task.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", padding: "0.85rem 1.25rem" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "0.2rem" }}>{task.title}</div>
                  {task.description && (
                    <div style={{ fontSize: "0.83rem", color: "var(--color-text-muted)", marginBottom: "0.5rem", lineHeight: 1.45 }}>
                      {task.description}
                    </div>
                  )}
                  <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexWrap: "wrap" }}>
                    <span className={`badge badge-${task.status}`}>{task.status.replace("_", " ")}</span>
                    <span className={`badge badge-${task.priority}`}>{task.priority}</span>
                    {task.assignee_email && (
                      <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                        {task.assignee_email}
                      </span>
                    )}
                    {task.due_date && (
                      <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                        Due {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                    <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
                      by {task.created_by_email}
                    </span>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", alignItems: "flex-end" }}>
                  <select
                    value={task.status}
                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                    style={{ width: "auto", fontSize: "0.8rem", padding: "0.3rem 1.5rem 0.3rem 0.5rem" }}
                    disabled={
                      !canManage(task) &&
                      task.assignee !== user?.id &&
                      task.created_by !== user?.id
                    }
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s.replace("_", " ")}</option>
                    ))}
                  </select>
                  {canManage(task) && (
                    <div style={{ display: "flex", gap: "0.3rem" }}>
                      <button className="btn-secondary" style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }} onClick={() => handleEdit(task)}>
                        Edit
                      </button>
                      <button className="btn-danger" style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }} onClick={() => setConfirmDelete(task)}>
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <Pagination count={count} next={next} previous={previous} onPage={setPage} />
        </>
      )}

      {confirmDelete && (
        <ConfirmDialog
          message={`Delete "${confirmDelete.title}"?`}
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </Layout>
  );
}