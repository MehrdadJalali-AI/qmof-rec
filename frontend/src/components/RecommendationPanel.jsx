import { useState } from "react";

import { Sparkles } from "lucide-react";

import { recommendMaterials } from "../api/api";

import MaterialCard from "./MaterialCard";

import MetricsDashboard from "./MetricsDashboard";

import LoadingSpinner from "./LoadingSpinner";

import { useRecommendation } from "../context/RecommendationContext";

export default function RecommendationPanel() {
  const { recommendation, recordRecommendation } = useRecommendation();

  // Only transient, request-in-flight UI state stays local. Everything
  // about the actual recommendation (results, weights, top material) is
  // read from the shared context, so this panel always shows the same
  // data as the Analytics page and the Dashboard's Material Metrics
  // sidebar - no more stale/mismatched views when switching tabs.
  const [query, setQuery] = useState(recommendation?.query || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const recommendations = recommendation?.results || [];
  const weights = recommendation?.weights || {};
  const optimizationMethod = recommendation?.optimizationMethod || "";
  const candidatePool = recommendation?.candidatePoolSize || null;
  const topMaterial = recommendations[0] || null;

  async function handleRecommend() {
    if (!query.trim()) return;

    setLoading(true);
    setError("");

    try {
      const data = await recommendMaterials(query, 5);
      const recs = data?.recommendations || [];

      recordRecommendation({
        query,
        results: recs,
        weights: data?.weights || {},
        optimizationMethod: data?.optimization_method || "",
        candidatePoolSize: data?.candidate_pool_size || null,
        generatedAt: Date.now(),
      });
    } catch (err) {
      console.log(err);

      setError("Recommendation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <div className="section-header">
        <h2>
          <Sparkles size={22} />
          AI Scientific Recommendation
        </h2>
      </div>

      <textarea
        className="textarea"
        rows={5}
        placeholder="Example: porous MOFs for CO2 adsorption"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button
        className="primary-btn"
        onClick={handleRecommend}
        disabled={loading}
      >
        {loading ? "Running LEA Optimization..." : "Generate Recommendations"}
      </button>

      {loading && <LoadingSpinner />}

      {error && <div className="error-box">{error}</div>}

      {optimizationMethod && (
        <div className="optimization-box">
          <div>
            <strong>Optimization:</strong> {optimizationMethod}
          </div>

          {candidatePool && (
            <div>
              <strong>Candidate Pool:</strong> {candidatePool}
            </div>
          )}
        </div>
      )}

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

      {!loading && recommendations.length === 0 && !error && (
        <div className="empty-state">No recommendations yet</div>
      )}
    </section>
  );
}