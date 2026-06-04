import { useState } from "react";

import { Award, Atom, BadgeInfo, CheckCircle, Eye, X } from "lucide-react";

import { getMaterialStructure } from "../api/api";

import MoleculeViewer from "./MoleculeViewer";

export default function MaterialCard({ material, rank }) {
  const [showStructure, setShowStructure] = useState(false);

  const [loadingStructure, setLoadingStructure] = useState(false);

  const [cifText, setCifText] = useState("");

  async function handleStructureToggle() {
    if (showStructure) {
      closeViewer();

      return;
    }

    if (!material?.qmof_id) {
      alert("No structure available");

      return;
    }

    setLoadingStructure(true);

    try {
      const cif = await getMaterialStructure(material.qmof_id);

      if (!cif) {
        throw new Error("Empty CIF");
      }

      setCifText(cif);

      setShowStructure(true);
    } catch (error) {
      console.error(error);

      alert("Unable to load structure");
    } finally {
      setLoadingStructure(false);
    }
  }

  function closeViewer() {
    setShowStructure(false);

    setCifText("");
  }

  return (
    <div className="material-card">
      {/* HEADER */}

      <div className="material-header">
        <div>
          <h2>
            #{rank} {material.qmof_id || "Unknown"}
          </h2>

          <p>{material.formula || "No Formula"}</p>
        </div>

        <div className="score-badge">
          <Award size={16} />

          {material.lea_score ?? material.final_score ?? "N/A"}
        </div>
      </div>

      {/* STATS */}

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

        <div>
          <BadgeInfo size={16} />
          LEA Rank
          <strong>{material.lea_rank ?? "N/A"}</strong>
        </div>
      </div>

      {/* EXPLANATIONS */}

      <div className="explanation-list">
        {material.explanations?.map((item, index) => (
          <div key={index} className="explanation-chip">
            <CheckCircle size={14} />

            {item}
          </div>
        ))}
      </div>

      {/* STRUCTURE BUTTON */}

      <button
        type="button"
        className="secondary-btn structure-btn"
        onClick={handleStructureToggle}
        disabled={loadingStructure}
      >
        <Eye size={16} />

        {loadingStructure
          ? "Loading Structure..."
          : showStructure
            ? "Hide Structure"
            : "View 3D Structure"}
      </button>

      {/* VIEWER */}

      {showStructure && cifText && (
        <div className="viewer-wrapper">
          <button type="button" className="viewer-close" onClick={closeViewer}>
            <X size={18} />
          </button>

          <MoleculeViewer
            key={`${material.qmof_id}-${showStructure}`}
            cifText={cifText}
          />
        </div>
      )}
    </div>
  );
}
