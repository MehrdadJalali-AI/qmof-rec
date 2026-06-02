import { Award, Atom, BadgeInfo, CheckCircle } from "lucide-react";

export default function MaterialCard({
  material,

  rank,
}) {
  return (
    <div className="material-card">
      <div className="material-header">
        <div>
          <h2>
            #{rank} {material.qmof_id || "Unknown"}
          </h2>

          <p>{material.formula || "No Formula"}</p>
        </div>

        <div className="score-badge">
          <Award size={16} />

          {material.final_score ?? 0}
        </div>
      </div>

      <div className="material-stats">
        <div>
          <Atom size={16} />
          Band Gap
          <strong>{material.band_gap ?? "N/A"}</strong>
        </div>

        <div>
          <BadgeInfo size={16} />
          Density
          <strong>{material.density ?? "N/A"}</strong>
        </div>

        <div>
          <BadgeInfo size={16} />
          Void Fraction
          <strong>{material.void_fraction ?? "N/A"}</strong>
        </div>
      </div>

      <div className="explanation-list">
        {material.explanations?.map(
          (
            item,

            index,
          ) => (
            <div className="explanation-chip" key={index}>
              <CheckCircle size={14} />

              {item}
            </div>
          ),
        )}
      </div>
    </div>
  );
}
