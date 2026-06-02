import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function MetricsDashboard() {
  const data = [
    { name: "Band Gap", value: 2.1 },
    { name: "Density", value: 0.8 },
    { name: "Porosity", value: 0.9 },
    { name: "Score", value: 0.88 },
  ];

  return (
    <section className="card">
      <h2>Material Metrics</h2>

      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip />
            <Bar dataKey="value" fill="#38bdf8" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
