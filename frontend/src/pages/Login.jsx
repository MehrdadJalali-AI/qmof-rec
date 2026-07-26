import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Atom, Loader2, TriangleAlert } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import AuthLattice from "../components/AuthLattice";

export default function Login() {
  const { login, error } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    const ok = await login(email, password);
    setSubmitting(false);
    if (ok) navigate("/");
  }

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <AuthLattice />

        <div className="auth-hero-top">
          <span className="mark"><Atom size={18} /></span>
          QMOF-Rec
        </div>

        <div className="auth-hero-copy">
          <h1>
            AI-guided discovery for{" "}
            <span className="brand-gradient-text">metal-organic frameworks</span>
          </h1>
          <p>
            Graph neural networks, retrieval-augmented chat, and multi-objective
            ranking — built on the QMOF database to help you find and reason
            about novel porous materials faster.
          </p>

          <div className="auth-hero-stats">
            <div>
              <strong>20K+</strong>
              <span>QMOF structures</span>
            </div>
            <div>
              <strong>GNN</strong>
              <span>Property prediction</span>
            </div>
            <div>
              <strong>RAG</strong>
              <span>Literature-grounded chat</span>
            </div>
          </div>
        </div>

        <div className="auth-hero-footer">qmof-rec / materials-intelligence-platform</div>
      </section>

      <section className="auth-form-side">
        <div className="auth-card">
          <div className="auth-card-logo">
            <span className="mark"><Atom size={16} /></span>
            <strong>QMOF-Rec</strong>
          </div>

          <h2>Welcome back</h2>
          <p className="auth-card-subtitle">Sign in to continue your research session.</p>

          {error && (
            <div className="auth-error">
              <TriangleAlert size={16} style={{ flexShrink: 0, marginTop: 1 }} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label className="auth-field-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="input"
              placeholder="you@institution.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />

            <label className="auth-field-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />

            <button type="submit" className="primary-btn auth-submit" disabled={submitting}>
              {submitting ? <Loader2 size={16} className="spin" /> : null}
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="auth-divider">new here</div>

          <p className="auth-switch">
            Don't have an account?
            <Link to="/register" className="auth-switch-link">Create one</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
