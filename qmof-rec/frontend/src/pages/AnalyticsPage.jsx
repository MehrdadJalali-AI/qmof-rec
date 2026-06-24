import MetricsDashboard from "../components/MetricsDashboard";

export default function AnalyticsPage() {
  return (
    <>
      <div className="header">
        <div>
          <div className="page-title">Analytics</div>
          <div className="subtitle">
            Visualize material properties and retrieval outputs.
          </div>
        </div>
      </div>

      <MetricsDashboard />
    </>
  );
}
