import { createContext, useContext, useState } from "react";

const RecommendationContext = createContext(null);

export function RecommendationProvider({ children }) {
  const [recommendation, setRecommendation] = useState(null);
  // recommendation shape when set:
  // {
  //   query: string,
  //   results: array of material objects (qmof_id, band_gap, density, void_fraction,
  //            final_score, novelty_score, semantic_score, feedback_boost, ...),
  //   weights: object,
  //   optimizationMethod: string,
  //   candidatePoolSize: number | null,
  //   generatedAt: number (Date.now())
  // }

  function recordRecommendation(data) {
    setRecommendation(data);
  }

  function clearRecommendation() {
    setRecommendation(null);
  }

  return (
    <RecommendationContext.Provider
      value={{ recommendation, recordRecommendation, clearRecommendation }}
    >
      {children}
    </RecommendationContext.Provider>
  );
}

export function useRecommendation() {
  const ctx = useContext(RecommendationContext);
  if (!ctx) {
    throw new Error(
      "useRecommendation must be used within a RecommendationProvider",
    );
  }
  return ctx;
}
