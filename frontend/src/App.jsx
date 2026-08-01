import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { RecommendationProvider } from "./context/RecommendationContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import AppBackground from "./components/AppBackground";
import Dashboard from "./pages/Dashboard";
import ChatPage from "./pages/ChatPage";
import ResearchPage from "./pages/ResearchPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import Login from "./pages/Login";
import Register from "./pages/Register";

function Workspace() {
  const [activePage, setActivePage] = useState("dashboard");

  function renderPage() {
    if (activePage === "chat") return <ChatPage />;
    if (activePage === "research") return <ResearchPage />;
    if (activePage === "analytics") return <AnalyticsPage />;

    return <Dashboard />;
  }

  return (
    <RecommendationProvider>
      <AppBackground />
      <div className="app-shell">
        <Sidebar activePage={activePage} setActivePage={setActivePage} />
        <main className="main">{renderPage()}</main>
      </div>
    </RecommendationProvider>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Workspace />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
