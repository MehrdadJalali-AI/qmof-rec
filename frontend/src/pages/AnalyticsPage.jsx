import RecommendationAnalytics from "../components/RecommendationAnalytics";

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

      <RecommendationAnalytics />
    </>
  );
}
