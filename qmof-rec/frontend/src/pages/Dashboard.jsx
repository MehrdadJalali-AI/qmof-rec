import { useEffect, useState } from "react";

import RecommendationPanel from "../components/RecommendationPanel";
import ChatWindow from "../components/ChatWindow";
import MetricsDashboard from "../components/MetricsDashboard";

import { healthCheck } from "../api/api";

export default function Dashboard() {
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    let cancelled = false;

    healthCheck()
      .then(() => {
        if (!cancelled) setBackendStatus("online");
      })
      .catch(() => {
        if (!cancelled) setBackendStatus("offline");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <div className="header">
        <div>
          <div className="page-title">AI Materials Discovery Workspace</div>
          <div className="subtitle">
            RAG-powered QMOF recommender, scientific chat, and graph-aware
            material discovery.
          </div>
        </div>

        <div className={`status-pill ${backendStatus === "offline" ? "offline" : ""}`}>
          {backendStatus === "online" && "Backend Connected"}
          {backendStatus === "offline" && "Backend Unreachable"}
          {backendStatus === "checking" && "Checking Backend..."}
        </div>
      </div>

      <div className="grid">
        <div>
          <RecommendationPanel />
        </div>

        <div>
          <MetricsDashboard />
        </div>
      </div>

      <div style={{ marginTop: 22 }}>
        <ChatWindow />
      </div>
    </>
  );
}
