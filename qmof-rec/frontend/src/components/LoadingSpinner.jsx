export default function LoadingSpinner({ label = "Loading..." }) {
  return (
    <div className="spinner-wrapper">
      <span className="spinner-ring" />
      <span>{label}</span>
    </div>
  );
}
