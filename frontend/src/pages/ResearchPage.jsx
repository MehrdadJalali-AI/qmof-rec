import RecommendationPanel from "../components/RecommendationPanel";

export default function ResearchPage() {
  return (
    <>
      <div className="header">
        <div>
          <div className="page-title">Research Workspace</div>
          <div className="subtitle">
            Explore candidate MOFs for target applications.
          </div>
        </div>
      </div>

      <RecommendationPanel />
    </>
  );
}
