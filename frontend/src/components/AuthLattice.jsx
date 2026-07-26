const NODES = [
  { x: 60, y: 80 },
  { x: 180, y: 50 },
  { x: 300, y: 110 },
  { x: 120, y: 200 },
  { x: 260, y: 230 },
  { x: 380, y: 170 },
  { x: 40, y: 320 },
  { x: 200, y: 350 },
  { x: 340, y: 320 },
  { x: 420, y: 60 },
  { x: 100, y: 430 },
  { x: 300, y: 440 },
  { x: 420, y: 410 },
  { x: 20, y: 200 },
];

const EDGES = [
  [0, 1],
  [1, 2],
  [1, 3],
  [2, 5],
  [3, 4],
  [4, 5],
  [4, 7],
  [5, 8],
  [5, 9],
  [6, 3],
  [6, 7],
  [6, 13],
  [7, 8],
  [7, 10],
  [8, 9],
  [8, 12],
  [10, 11],
  [11, 12],
  [3, 13],
  [0, 13],
];

export default function AuthLattice() {
  return (
    <svg
      className="auth-hero-lattice"
      viewBox="0 0 440 460"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <linearGradient id="latticeLineGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#e8a87c" />
          <stop offset="100%" stopColor="#a8503a" />
        </linearGradient>
      </defs>

      {EDGES.map(([a, b], i) => (
        <line
          key={`e-${i}`}
          x1={NODES[a].x}
          y1={NODES[a].y}
          x2={NODES[b].x}
          y2={NODES[b].y}
          strokeWidth="1"
        />
      ))}

      {NODES.map((n, i) => (
        <circle
          key={`n-${i}`}
          cx={n.x}
          cy={n.y}
          r="2.6"
          fill="#dba07c"
          style={{ animationDelay: `${(i % 6) * 0.4}s` }}
        />
      ))}
    </svg>
  );
}
