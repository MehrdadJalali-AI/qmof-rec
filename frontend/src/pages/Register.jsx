import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Atom, Loader2, TriangleAlert } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import AuthLattice from "../components/AuthLattice";

function passwordScore(password) {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score;
}

export default function Register() {
  const { register, error } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const strength = useMemo(() => passwordScore(password), [password]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    const ok = await register(email, password, fullName);
    setSubmitting(false);
    if (ok) navigate("/");
  }

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <AuthLattice />

        <div className="auth-hero-top">
          <span className="mark">
            <Atom size={18} />
          </span>
          QMOF-Rec
        </div>

        <div className="auth-hero-copy">
          <h1>
            Join the search for the next{" "}
            <span className="brand-gradient-text">breakthrough material</span>
          </h1>
          <p>
            Create an account to save queries, bookmark candidate structures,
            and pick up your research exactly where you left off.
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

        <div className="auth-hero-footer">
          qmof-rec / materials-intelligence-platform
        </div>
      </section>

      <section className="auth-form-side">
        <div className="auth-card">
          <div className="auth-card-logo">
            <span className="mark">
              <Atom size={16} />
            </span>
            <strong>QMOF-Rec</strong>
          </div>

          <h2>Create your account</h2>
          <p className="auth-card-subtitle">
            Start exploring the QMOF database with AI assistance.
          </p>

          {error && (
            <div className="auth-error">
              <TriangleAlert
                size={16}
                style={{ flexShrink: 0, marginTop: 1 }}
              />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label className="auth-field-label" htmlFor="fullName">
              Full name
            </label>
            <input
              id="fullName"
              type="text"
              className="input"
              placeholder="Ada Lovelace"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
            />

            <label className="auth-field-label" htmlFor="email">
              Email
            </label>
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

            <label className="auth-field-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="input"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
              minLength={8}
            />

            {password.length > 0 && (
              <div className="password-strength">
                {[0, 1, 2, 3].map((i) => (
                  <span
                    key={i}
                    style={{
                      background:
                        i < strength
                          ? ["#e0867a", "#d9b36a", "#cc785c", "#7fb88f"][
                              strength - 1
                            ]
                          : undefined,
                    }}
                  />
                ))}
              </div>
            )}

            <button
              type="submit"
              className="primary-btn auth-submit"
              disabled={submitting}
            >
              {submitting ? <Loader2 size={16} className="spin" /> : null}
              {submitting ? "Creating account…" : "Create account"}
            </button>
          </form>

          <div className="auth-divider">already a member</div>

          <p className="auth-switch">
            Already have an account?
            <Link to="/login" className="auth-switch-link">
              Sign in
            </Link>
          </p>
        </div>
      </section>
    </div>
  );
}
