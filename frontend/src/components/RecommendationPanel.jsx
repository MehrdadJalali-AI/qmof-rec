import { useState } from "react";

import { Sparkles } from "lucide-react";

import { recommendMaterials } from "../api/api";

import MaterialCard from "./MaterialCard";

export default function RecommendationPanel() {
  const [query, setQuery] = useState("");

  const [loading, setLoading] = useState(false);

  const [recommendations, setRecommendations] = useState([]);

  const [weights, setWeights] = useState({});

  const [optimization, setOptimization] = useState(null);

  async function handleRecommend() {
    if (!query.trim()) return;

    setLoading(true);

    setRecommendations([]);

    setWeights({});

    setOptimization(null);

    try {
      const data = await recommendMaterials(
        query,

        5,
      );

      setRecommendations(data.recommendations || []);

      setWeights(data.weights || {});

      setOptimization(data.optimization || null);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>
        <Sparkles size={22} />
        AI Scientific Recommendation
      </h2>

      <textarea
        className="textarea"
        rows={5}
        placeholder="Example: stable porous MOFs for CO2 adsorption"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button className="primary-btn" onClick={handleRecommend}>
        {loading ? "Generating..." : "Generate Recommendations"}
      </button>

      {Object.keys(weights).length > 0 && (
        <div className="weights-card">
          <h3>Dynamic Scientific Weights</h3>

          {Object.entries(weights)

            .map(([k, v]) => (
              <div key={k}>
                <strong>{k}</strong>
                {" : "}
                {(v * 100).toFixed(1)}%
              </div>
            ))}
        </div>
      )}

      {optimization && (
        <div className="weights-card">
          <h3>LEA Optimization</h3>

          <div>
            <strong>method</strong>
            {" : "}
            {optimization.method}
          </div>

          <div>
            <strong>candidate pool</strong>
            {" : "}
            {optimization.candidate_pool_size}
          </div>

          <div>
            <strong>population</strong>
            {" : "}
            {optimization.population_size}
          </div>

          <div>
            <strong>iterations</strong>
            {" : "}
            {optimization.iterations}
          </div>

          <div>
            <strong>diversity</strong>
            {" : "}
            {Number(optimization.diversity_score || 0).toFixed(4)}
          </div>
        </div>
      )}

      <div className="rec-list">
        {recommendations.map(
          (
            item,

            index,
          ) => (
            <MaterialCard
              key={item.qmof_id + index}
              material={item}
              rank={index + 1}
            />
          ),
        )}
      </div>
    </section>
  );
}
