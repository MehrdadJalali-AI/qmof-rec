import { useState } from "react";

import { Award, Atom, BadgeInfo, CheckCircle, Eye, X } from "lucide-react";

import { getMaterialStructure, submitFeedback } from "../api/api";

import MoleculeViewer from "./MoleculeViewer";
import ScoreSelector from "./ScoreSelector";

export default function MaterialCard({ material, rank, query }) {
  const [showStructure, setShowStructure] = useState(false);

  const [loadingStructure, setLoadingStructure] = useState(false);

  const [cifText, setCifText] = useState("");

  const [relevance, setRelevance] = useState("");

  const [usefulness, setUsefulness] = useState("");

  const [feedbackSaved, setFeedbackSaved] = useState(false);

  const [submittingFeedback, setSubmittingFeedback] = useState(false);

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
        throw new Error();
      }

      setCifText(cif);

      setShowStructure(true);
    } catch (error) {
      console.log(error);

      alert("Unable to load structure");
    } finally {
      setLoadingStructure(false);
    }
  }

  function closeViewer() {
    setShowStructure(false);

    setCifText("");
  }

  async function handleFeedback() {
    if (relevance === "" || usefulness === "") {
      alert("Please provide feedback");

      return;
    }

    setSubmittingFeedback(true);

    try {
      await submitFeedback(
        query,

        material.qmof_id,

        relevance,

        usefulness,
      );

      setFeedbackSaved(true);
    } catch (error) {
      console.log(error);

      alert("Feedback failed");
    } finally {
      setSubmittingFeedback(false);
    }
  }

  return (
    <div className="material-card">
      {/* HEADER */}

      <div className="material-header">
        <div>
          <h2>
            #{material.lea_rank || rank} {material.qmof_id || "Unknown"}
          </h2>

          <p>{material.formula || "No Formula"}</p>
        </div>

        <div>
          <div className="score-badge">
            <Award size={16} />

            {material.final_score ?? "N/A"}
          </div>

          <div className="mini-badge">LEA #{material.lea_rank || rank}</div>
        </div>
      </div>

      {/* BADGES */}

      <div className="badge-row">
        <div className="mini-badge">
          Novelty: {material.novelty_score ?? "N/A"}
        </div>

        <div className="mini-badge">
          Feedback: {material.feedback_boost ?? "N/A"}
        </div>

        <div className="mini-badge">
          Semantic: {material.semantic_score ?? "N/A"}
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
          ? "Loading..."
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
            key={material.qmof_id + showStructure}
            cifText={cifText}
          />
        </div>
      )}

      {/* PROFESSIONAL FEEDBACK */}

      <div className="professional-feedback">
        <div className="feedback-header">
          <div>
            <h4>Query-Specific Feedback</h4>

            <p>Help improve future recommendations for similar queries</p>
          </div>

          {feedbackSaved && <span className="feedback-status">Saved</span>}
        </div>

        <div className="feedback-grid">
          <div className="feedback-field">
            <label>Relevance</label>

            <ScoreSelector
              value={relevance}
              onChange={setRelevance}
              disabled={feedbackSaved}
            />
          </div>

          <div className="feedback-field">
            <label>Usefulness</label>

            <ScoreSelector
              value={usefulness}
              onChange={setUsefulness}
              disabled={feedbackSaved}
            />
          </div>
        </div>

        <button
          type="button"
          className="feedback-submit-btn"
          disabled={feedbackSaved || submittingFeedback}
          onClick={handleFeedback}
        >
          {submittingFeedback
            ? "Saving Feedback..."
            : feedbackSaved
              ? "Feedback Saved"
              : "Submit Feedback"}
        </button>
      </div>
    </div>
  );
}
