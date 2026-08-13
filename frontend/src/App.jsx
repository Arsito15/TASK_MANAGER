import { Routes, Route, Navigate, useParams } from "react-router-dom";

import { useAuth } from "./context/AuthContext.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import OrganizationList from "./pages/OrganizationList.jsx";
import OrganizationDetail from "./pages/OrganizationDetail.jsx";
import ProjectDetail from "./pages/ProjectDetail.jsx";
import NotFound from "./pages/NotFound.jsx";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading...</div>;
  if (isAuthenticated) return <Navigate to="/" replace />;
  return children;
}

function OrgDetailWrapper() {
  const params = useParams();
  return <OrganizationDetail params={params} />;
}

function ProjectDetailWrapper() {
  const params = useParams();
  return <ProjectDetail params={params} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      <Route path="/" element={<ProtectedRoute><OrganizationList /></ProtectedRoute>} />
      <Route path="/orgs/:slug" element={<ProtectedRoute><OrgDetailWrapper /></ProtectedRoute>} />
      <Route path="/projects/:id" element={<ProtectedRoute><ProjectDetailWrapper /></ProtectedRoute>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}