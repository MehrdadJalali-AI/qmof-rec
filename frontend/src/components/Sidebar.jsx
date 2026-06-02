import {
  LayoutDashboard,
  MessageSquare,
  FlaskConical,
  BarChart3,
} from "lucide-react";

export default function Sidebar({ activePage, setActivePage }) {
  const items = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "chat", label: "Chat", icon: MessageSquare },
    { id: "research", label: "Research", icon: FlaskConical },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
  ];

  return (
    <aside className="sidebar">
      <div className="logo">QMOF AI</div>

      {items.map((item) => {
        const Icon = item.icon;

        return (
          <button
            key={item.id}
            className={`nav-btn ${activePage === item.id ? "active" : ""}`}
            onClick={() => setActivePage(item.id)}
          >
            <Icon size={16} /> {item.label}
          </button>
        );
      })}
    </aside>
  );
}
