import { useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const res = await apiClient.post("/auth/login", { email, password });
      localStorage.setItem("access_token", res.data.access_token);
      navigate("/enrollment");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <form onSubmit={handleLogin} className="card w-full max-w-sm space-y-4">
        <h1 className="text-xl font-semibold">Ambient AI</h1>
        <p className="text-sm text-gray-400">Clinician sign in</p>
        <input
          className="w-full bg-panel2 border border-border rounded-xl px-3 py-2 text-sm"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="w-full bg-panel2 border border-border rounded-xl px-3 py-2 text-sm"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button type="submit" className="btn-primary w-full">
          Log in
        </button>
      </form>
    </div>
  );
}
