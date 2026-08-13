import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : "?";

  return (
    <div>
      <header className="app-header">
        <Link to="/" className="app-logo">
          <span className="app-logo-icon">T</span>
          TaskManager
        </Link>
        {user && (
          <div className="user-chip">
            <span className="user-email">{user.email}</span>
            <div className="user-avatar">{initials}</div>
            <button className="btn-secondary" onClick={handleLogout} style={{ marginLeft: "0.5rem" }}>
              Logout
            </button>
          </div>
        )}
      </header>
      <div className="page-container">{children}</div>
    </div>
  );
}