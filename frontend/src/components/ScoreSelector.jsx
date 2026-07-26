const LABELS = {
  1: "Poor",
  2: "Weak",
  3: "OK",
  4: "Good",
  5: "Excellent",
};

export default function ScoreSelector({
  value,
  onChange,
  max = 5,
  disabled = false,
}) {
  return (
    <div className={`score-selector ${disabled ? "is-disabled" : ""}`}>
      <div className="score-pill-row">
        {Array.from({ length: max }, (_, i) => i + 1).map((n) => {
          const active = value === n;
          return (
            <button
              key={n}
              type="button"
              className={`score-pill ${active ? "active" : ""}`}
              onClick={() => !disabled && onChange(n)}
              disabled={disabled}
              aria-pressed={active}
              title={LABELS[n]}
            >
              {n}
            </button>
          );
        })}
      </div>
      <span className="score-pill-caption">
        {value ? LABELS[value] : "Tap to rate"}
      </span>
    </div>
  );
}
