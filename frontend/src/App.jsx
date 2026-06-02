import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import ChatPage from "./pages/ChatPage";
import ResearchPage from "./pages/ResearchPage";
import AnalyticsPage from "./pages/AnalyticsPage";

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");

  function renderPage() {
    if (activePage === "chat") return <ChatPage />;
    if (activePage === "research") return <ResearchPage />;
    if (activePage === "analytics") return <AnalyticsPage />;

    return <Dashboard />;
  }

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <main className="main">{renderPage()}</main>
    </div>
  );
}
