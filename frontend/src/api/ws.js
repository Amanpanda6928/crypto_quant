export const connectWS = (setData) => {
  const ws = new WebSocket("ws://127.0.0.1:8000/ws/live");

  ws.onmessage = (e) => setData(JSON.parse(e.data));

  return ws;
};
