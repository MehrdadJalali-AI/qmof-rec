import {
  LayoutDashboard,
  MessageSquare,
  FlaskConical,
  BarChart3,
  Sun,
  Moon,
  LogOut,
} from "lucide-react";

import logo from "../assests/QMOF-Rec.svg";
import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";

export default function Sidebar({ activePage, setActivePage }) {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  const items = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      id: "chat",
      label: "Chat",
      icon: MessageSquare,
    },
    {
      id: "research",
      label: "Research",
      icon: FlaskConical,
    },
    {
      id: "analytics",
      label: "Analytics",
      icon: BarChart3,
    },
  ];

  const initials = (user?.full_name || user?.email || "?")
    .trim()
    .split(/\s+/)
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <aside className="sidebar">
      {/* LOGO */}
      <div className="sidebar-logo">
        <img src={logo} alt="QMOF-Rec" />
      </div>

      {/* NAVIGATION */}
      <div className="sidebar-section-label">Workspace</div>
      <div className="sidebar-menu">
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              type="button"
              className={`nav-btn ${activePage === item.id ? "active" : ""}`}
              onClick={() => setActivePage(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* THEME TOGGLE */}
      <button type="button" className="theme-toggle" onClick={toggleTheme}>
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
      </button>

      {/* ACCOUNT */}
      {user && (
        <div className="sidebar-account">
          <div className="sidebar-account-avatar">{initials}</div>
          <div className="sidebar-account-info">
            <strong>{user.full_name || "Researcher"}</strong>
            <span>{user.email}</span>
          </div>
          <button
            type="button"
            className="sidebar-account-logout"
            onClick={logout}
            title="Sign out"
          >
            <LogOut size={15} />
          </button>
        </div>
      )}

      {/* FOOTER */}
      <div className="sidebar-footer">
        <strong>QMOF-Rec</strong>
        <span>Multi-Objective MOF Recommendation</span>
      </div>
    </aside>
  );
}
