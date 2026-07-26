import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Sparkles } from "lucide-react";

import { useRecommendation } from "../context/RecommendationContext";

function safeNum(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return Number(value);
}

function shortId(qmofId, index) {
  if (!qmofId) return `#${index + 1}`;
  return qmofId.length > 12 ? qmofId.slice(0, 12) + "\u2026" : qmofId;
}

const CHART_COLORS = {
  band_gap: "var(--accent)",
  density: "var(--accent-strong)",
  final_score: "var(--accent)",
  novelty_score: "var(--accent-strong)",
  semantic_score: "#5b5470",
  feedback_boost: "#1f6f56",
};

function computeStats(values) {
  const valid = values.filter(
    (v) => v !== null && v !== undefined && !Number.isNaN(v),
  );
  if (valid.length === 0) {
    return { count: 0, min: null, max: null, mean: null, median: null };
  }
  const sorted = [...valid].sort((a, b) => a - b);
  const n = sorted.length;
  const mean = sorted.reduce((a, b) => a + b, 0) / n;
  const median =
    n % 2 === 1 ? sorted[(n - 1) / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2;
  return {
    count: n,
    min: sorted[0],
    max: sorted[n - 1],
    mean,
    median,
  };
}

function round(value, digits = 3) {
  if (value === null || value === undefined) return "\u2014";
  return Number(value.toFixed(digits));
}

function PropertyBarChart({ title, unit, dataKey, results }) {
  const data = results.map((m, i) => ({
    name: shortId(m.qmof_id, i),
    value: safeNum(m[dataKey]),
  }));

  const stats = computeStats(data.map((d) => d.value));
  const hasAnyValue = stats.count > 0;
  const missingCount = results.length - stats.count;

  return (
    <div className="dataset-property-card">
      <div className="dataset-property-header">
        <h3>
          {title}
          {unit ? <span className="dataset-unit"> ({unit})</span> : null}
        </h3>
        {hasAnyValue && (
          <span className="dataset-coverage-pill">
            {stats.count}/{results.length} have data
          </span>
        )}
      </div>

      {!hasAnyValue ? (
        <div className="empty-state" style={{ marginTop: 8 }}>
          None of the returned materials have {title.toLowerCase()} data
          available.
        </div>
      ) : (
        <>
          <div className="dataset-property-stats">
            <div>
              <span>Min</span>
              <strong>{round(stats.min)}</strong>
            </div>
            <div>
              <span>Mean</span>
              <strong>{round(stats.mean)}</strong>
            </div>
            <div>
              <span>Median</span>
              <strong>{round(stats.median)}</strong>
            </div>
            <div>
              <span>Max</span>
              <strong>{round(stats.max)}</strong>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={180}>
            <BarChart
              data={data}
              margin={{ top: 8, right: 8, left: -20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="name"
                stroke="var(--muted)"
                tick={{ fill: "var(--muted)", fontSize: 10.5 }}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
              />
              <YAxis
                stroke="var(--muted)"
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-strong)",
                  borderRadius: 10,
                  color: "var(--text)",
                  fontSize: 12.5,
                }}
                cursor={{ fill: "var(--accent-soft)" }}
              />
              <Bar
                dataKey="value"
                fill={CHART_COLORS[dataKey]}
                radius={[5, 5, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>

          {missingCount > 0 && (
            <p className="dataset-missing-note">
              {missingCount} of {results.length} returned materials don't have
              this property computed.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function ScoreComparisonChart({ results }) {
  const data = results.map((m, i) => ({
    name: shortId(m.qmof_id, i),
    "Final Score": safeNum(m.final_score) ?? 0,
    Novelty: safeNum(m.novelty_score) ?? 0,
    Semantic: safeNum(m.semantic_score) ?? 0,
    Feedback: safeNum(m.feedback_boost) ?? 0,
  }));

  return (
    <div className="card" style={{ marginTop: 18 }}>
      <h2>
        <Sparkles size={20} />
        Score Breakdown by Candidate
      </h2>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--border)"
            vertical={false}
          />
          <XAxis
            dataKey="name"
            stroke="var(--muted)"
            tick={{ fill: "var(--muted)", fontSize: 11.5 }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            stroke="var(--muted)"
            tick={{ fill: "var(--muted)", fontSize: 11.5 }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-strong)",
              borderRadius: 10,
              color: "var(--text)",
              fontSize: 12.5,
            }}
            cursor={{ fill: "var(--accent-soft)" }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12.5, color: "var(--text-soft)" }}
          />
          <Bar
            dataKey="Final Score"
            fill="var(--accent)"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="Novelty"
            fill="var(--accent-strong)"
            radius={[4, 4, 0, 0]}
          />
          <Bar dataKey="Semantic" fill="#5b5470" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Feedback" fill="#1f6f56" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function RecommendationAnalytics() {
  const { recommendation } = useRecommendation();

  if (!recommendation || !recommendation.results?.length) {
    return (
      <div className="card">
        <h2>
          <Sparkles size={20} />
          Recommendation Analysis
        </h2>
        <div className="empty-state">
          Generate a recommendation on the Dashboard or Research page to see an
          analysis of the returned materials here.
        </div>
      </div>
    );
  }

  const { query, results, optimizationMethod, candidatePoolSize } =
    recommendation;

  return (
    <>
      <div className="card">
        <h2>
          <Sparkles size={20} />
          Recommendation Analysis
        </h2>
        <p className="subtitle" style={{ marginTop: -10, marginBottom: 4 }}>
          Analyzing the {results.length} material
          {results.length === 1 ? "" : "s"} returned for:
        </p>
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 13.5,
            color: "var(--accent)",
            marginBottom: 18,
          }}
        >
          "{query}"
        </p>

        {(optimizationMethod || candidatePoolSize) && (
          <div className="optimization-box" style={{ marginTop: 0 }}>
            {optimizationMethod && (
              <div>
                <strong>Optimization:</strong> {optimizationMethod}
              </div>
            )}
            {candidatePoolSize && (
              <div>
                <strong>Candidate Pool:</strong> {candidatePoolSize}
              </div>
            )}
          </div>
        )}

        <div className="dataset-property-grid" style={{ marginTop: 18 }}>
          <PropertyBarChart
            title="Band Gap"
            unit="eV"
            dataKey="band_gap"
            results={results}
          />
          <PropertyBarChart
            title="Density"
            unit="g/cm\u00b3"
            dataKey="density"
            results={results}
          />
        </div>
      </div>

      <ScoreComparisonChart results={results} />
    </>
  );
}
