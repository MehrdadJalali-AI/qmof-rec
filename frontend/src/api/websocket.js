// NOTE: The backend does not currently expose a /ws endpoint.
// This connection will fail until that route is added server-side.
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://127.0.0.1:8000";

const socket = new WebSocket(`${WS_BASE_URL}/ws`);

export default socket;
