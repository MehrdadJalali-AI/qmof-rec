import { createContext, useContext, useEffect, useState } from "react";

import { fetchCurrentUser, loginUser, logoutUser, registerUser } from "../api/api";

const AuthContext = createContext(null);

const TOKEN_KEY = "qmof_access_token";
const REFRESH_KEY = "qmof_refresh_token";
const USER_KEY = "qmof_user";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = window.localStorage?.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = window.localStorage?.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }

    fetchCurrentUser()
      .then((freshUser) => {
        setUser(freshUser);
        window.localStorage?.setItem(USER_KEY, JSON.stringify(freshUser));
      })
      .catch(() => {
        clearSession();
      })
      .finally(() => setLoading(false));
  }, []);

  function persistSession(data) {
    window.localStorage?.setItem(TOKEN_KEY, data.access_token);
    window.localStorage?.setItem(REFRESH_KEY, data.refresh_token);
    window.localStorage?.setItem(USER_KEY, JSON.stringify(data.user));
    setUser(data.user);
  }

  async function login(email, password) {
    setError(null);
    try {
      const data = await loginUser(email, password);
      persistSession(data);
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
      return false;
    }
  }

  async function register(email, password, fullName) {
    setError(null);
    try {
      const data = await registerUser(email, password, fullName);
      persistSession(data);
      return true;
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : detail || "Registration failed."
      );
      return false;
    }
  }

  function clearSession() {
    window.localStorage?.removeItem(TOKEN_KEY);
    window.localStorage?.removeItem(REFRESH_KEY);
    window.localStorage?.removeItem(USER_KEY);
    setUser(null);
  }

  async function logout() {
    const refreshToken = window.localStorage?.getItem(REFRESH_KEY);
    clearSession();
    if (refreshToken) {
      // Best-effort: revoke server-side so the refresh token can't be
      // replayed later. Don't block the UI on this - the user is
      // logged out locally either way.
      try {
        await logoutUser(refreshToken);
      } catch {
        // Ignore - token may already be expired/revoked.
      }
    }
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, register, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
