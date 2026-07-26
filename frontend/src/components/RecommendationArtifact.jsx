import { Sparkles } from "lucide-react";

import MaterialCard from "./MaterialCard";
import MetricsDashboard from "./MetricsDashboard";

/**
 * Renders a recommendation result (weights, optimization info, candidate
 * cards, top-material metrics) as a self-contained "artifact" card.
 *
 * Used inline within the chat conversation when a query is detected as a
 * recommendation-style request.
 */
export default function RecommendationArtifact({ data, query }) {
  const recommendations = data?.recommendations || [];
  const weights = data?.weights || {};
  const optimizationMethod = data?.optimization_method || "";
  const candidatePool = data?.candidate_pool_size || null;
  const topMaterial = recommendations[0] || null;

  if (!recommendations.length) {
    return (
      <div className="rec-artifact">
        <div className="rec-artifact-header">
          <h3>
            <Sparkles size={16} />
            Recommendation
          </h3>
        </div>
        <div className="rec-artifact-body">
          <div className="empty-state">No matching candidates were found.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="rec-artifact">
      <div className="rec-artifact-header">
        <h3>
          <Sparkles size={16} />
          Recommended Candidates
        </h3>

        <div className="rec-artifact-meta">
          {optimizationMethod && (
            <span className="mini-badge">{optimizationMethod}</span>
          )}
          {candidatePool && (
            <span className="mini-badge">Pool: {candidatePool}</span>
          )}
          <span className="mini-badge">{recommendations.length} results</span>
        </div>
      </div>

      <div className="rec-artifact-body">
        {Object.keys(weights).length > 0 && (
          <div className="weights-card">
            <h3>Dynamic Weights</h3>

            {Object.entries(weights).map(([k, v]) => (
              <div key={k} className="weight-row">
                <span>{k}</span>
                <span>{(v * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        )}

        {topMaterial && <MetricsDashboard material={topMaterial} />}

        <div className="rec-list">
          {recommendations.map((item, index) => (
            <MaterialCard
              key={(item.qmof_id || index) + index}
              material={item}
              rank={item.lea_rank || index + 1}
              query={query}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
