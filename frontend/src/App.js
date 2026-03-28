import { useEffect, useState } from "react";
import Login from "./components/auth/Login";
import MainLayout from "./layout/MainLayout";

export default function App() {
  const [user, setUser] = useState(localStorage.getItem("token"));
  const [data, setData] = useState({});

  useEffect(() => {
    if (!user) return;

    const ws = new WebSocket("ws://127.0.0.1:8000/ws/live");

    ws.onmessage = (e) => {
      setData(JSON.parse(e.data));
    };

    return () => ws.close();
  }, [user]);

  return !user
    ? <Login setUser={setUser} />
    : <MainLayout data={data} />;
}
