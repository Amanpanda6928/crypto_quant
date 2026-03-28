import { useState } from "react";
import { api } from "../../api/http";

export default function Login({ setUser }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");

  const login = async () => {
    try {
      const res = await api.post("/login", { username: u, password: p });

      if (res.data.success) {
        localStorage.setItem("token", res.data.token);
        setUser(res.data.token);
      } else {
        alert("Login failed");
      }
    } catch (error) {
      console.error("Login error:", error);
      alert("Login error - check console");
    }
  };

  return (
    <div className="login">
      <h2>Login</h2>
      <input placeholder="user" onChange={e=>setU(e.target.value)} />
      <input type="password" onChange={e=>setP(e.target.value)} />
      <button onClick={login}>Login</button>
    </div>
  );
}
