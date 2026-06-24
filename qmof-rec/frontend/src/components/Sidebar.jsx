import {
  LayoutDashboard,
  MessageSquare,
  FlaskConical,
  BarChart3,
  Sun,
  Moon,
} from "lucide-react";

import logo from "../assests/QMOF-Rec.svg";
import { useTheme } from "../context/ThemeContext";

export default function Sidebar({ activePage, setActivePage }) {
  const { theme, toggleTheme } = useTheme();

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

      {/* FOOTER */}
      <div className="sidebar-footer">
        <strong>QMOF-Rec</strong>
        <span>Multi-Objective MOF Recommendation</span>
      </div>
    </aside>
  );
}
