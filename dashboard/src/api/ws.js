export function connectStatsSocket(onTrafficEvent, onHealth) {
  const socket = new WebSocket("ws://localhost:8000/ws/stats");

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "health") {
      onHealth(payload.data);
    } else {
      onTrafficEvent(payload);
    }
  };

  return socket;
}
