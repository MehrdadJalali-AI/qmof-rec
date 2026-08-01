import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Activity } from "lucide-react";

export default function MetricsDashboard({ material }) {
  function safeMetric(value) {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return 0;
    }

    return Number(value);
  }

  if (!material) {
    return (
      <div className="metric-card">
        <h2>
          <Activity size={20} />
          Material Metrics
        </h2>

        <div className="empty-state">
          Generate a recommendation to see property metrics for the
          top-ranked candidate here.
        </div>
      </div>
    );
  }

  const data = [
    {
      name: "Band Gap",
      value: safeMetric(material?.band_gap),
    },
    {
      name: "Density",
      value: safeMetric(material?.density),
    },
    {
      name: "Score",
      value: safeMetric(material?.final_score),
    },
    {
      name: "Semantic",
      value: safeMetric(material?.semantic_score),
    },
    {
      name: "Novelty",
      value: safeMetric(material?.novelty_score),
    },
    {
      name: "Feedback",
      value: safeMetric(material?.feedback_boost),
    },
  ];

  return (
    <div className="metric-card">
      <h2>
        <Activity size={20} />
        Material Metrics
      </h2>

      {material?.qmof_id && (
        <p
          style={{
            margin: "-10px 0 16px",
            fontSize: "12.5px",
            color: "var(--muted)",
            fontFamily: "'JetBrains Mono', Consolas, monospace",
          }}
        >
          {material.qmof_id}
        </p>
      )}

      {material?.void_fraction_note && (
        <p
          style={{
            margin: "-8px 0 16px",
            fontSize: "12.5px",
            color: "var(--muted)",
          }}
        >
          Void fraction {material.void_fraction_note}.
        </p>
      )}

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255, 255, 255, 0.08)"
            vertical={false}
          />
          <XAxis
            dataKey="name"
            stroke="var(--muted)"
            tick={{ fill: "#8b8b93", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255, 255, 255, 0.12)" }}
            tickLine={false}
          />
          <YAxis
            stroke="var(--muted)"
            tick={{ fill: "#8b8b93", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255, 255, 255, 0.12)" }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#16161a",
              border: "1px solid rgba(255, 255, 255, 0.16)",
              borderRadius: 12,
              color: "#f5f5f6",
              fontSize: 13,
            }}
            cursor={{ fill: "rgba(255, 255, 255, 0.04)" }}
          />
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f5f5f6" />
              <stop offset="100%" stopColor="#9a9aa1" />
            </linearGradient>
          </defs>
          <Bar dataKey="value" fill="url(#barGradient)" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
