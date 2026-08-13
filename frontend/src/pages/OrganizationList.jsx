import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";

import Layout from "../components/Layout.jsx";
import Spinner from "../components/Spinner.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { getMyOrganizations, createOrganization } from "../api/organizations";

export default function OrganizationList() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [creating, setCreating] = useState(false);

  const loadOrgs = useCallback(async () => {
    try {
      const data = await getMyOrganizations();
      setOrgs(data.results || data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrgs();
  }, [loadOrgs]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const newOrg = await createOrganization(newOrgName);
      setOrgs([newOrg, ...orgs]);
      setNewOrgName("");
      setShowForm(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Layout>
      <div className="page-header">
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 600, fontFamily: "var(--font-serif)", letterSpacing: "-0.02em" }}>
            My Organizations
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", marginTop: "0.25rem" }}>
            Organizations you belong to.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Organization"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card" style={{ marginBottom: "1.5rem" }}>
          <div className="form-group">
            <label>Organization Name</label>
            <input
              type="text"
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              placeholder="e.g. Acme Inc."
              required
              autoFocus
            />
          </div>
          <button type="submit" className="btn-primary" disabled={creating}>
            {creating ? "Creating…" : "Create Organization"}
          </button>
        </form>
      )}

      <ErrorBanner error={error} />

      {loading ? (
        <Spinner />
      ) : orgs.length === 0 ? (
        <EmptyState
          message="You don't belong to any organization yet."
          action={
            <button className="btn-primary" onClick={() => setShowForm(true)}>
              Create One
            </button>
          }
        />
      ) : (
        <div style={{ display: "grid", gap: "0.5rem" }}>
          {orgs.map((org) => (
            <Link
              key={org.id}
              to={`/orgs/${org.slug}`}
              className="card card-hover"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "1rem 1.25rem",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{org.name}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", marginTop: "0.2rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  Your role: <span className={`badge badge-${org.my_role}`}>{org.my_role}</span>
                </div>
              </div>
              <span style={{ color: "var(--color-text-muted)", fontSize: "1.1rem" }}>&rarr;</span>
            </Link>
          ))}
        </div>
      )}
    </Layout>
  );
}