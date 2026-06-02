import RecommendationPanel from "../components/RecommendationPanel";
import ChatWindow from "../components/ChatWindow";
import MetricsDashboard from "../components/MetricsDashboard";

export default function Dashboard() {
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

        <div className="status-pill">Backend Connected</div>
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
