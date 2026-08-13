import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { register } from "../api/auth";
import { useAuth } from "../context/AuthContext.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    if (form.password !== form.password2) {
      setErrors({ password2: "Passwords do not match." });
      return;
    }
    if (form.password.length < 8) {
      setErrors({ password: "Password must be at least 8 characters." });
      return;
    }
    setSubmitting(true);
    try {
      await register(form.username, form.email, form.password);
      await login(form.email, form.password);
      navigate("/");
    } catch (err) {
      if (err.data) {
        setErrors(err.data);
      } else {
        setErrors({ general: err.message });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "4rem auto", padding: "0 1rem" }}>
      <div className="card">
        <h1 style={{ fontSize: "1.5rem", marginBottom: "1.5rem" }}>Create Account</h1>
        <ErrorBanner error={errors.general} />
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              required
            />
            {errors.username && <div className="form-error">{errors.username}</div>}
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
            />
            {errors.email && <div className="form-error">{errors.email}</div>}
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
            />
            {errors.password && <div className="form-error">{errors.password}</div>}
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              name="password2"
              value={form.password2}
              onChange={handleChange}
              required
            />
            {errors.password2 && <div className="form-error">{errors.password2}</div>}
          </div>
          <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={submitting}>
            {submitting ? "Creating account..." : "Register"}
          </button>
        </form>
        <p style={{ marginTop: "1rem", textAlign: "center", fontSize: "0.9rem" }}>
          Already have an account? <Link to="/login">Sign In</Link>
        </p>
      </div>
    </div>
  );
}