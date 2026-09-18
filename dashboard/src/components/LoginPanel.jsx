import { useState } from "react";
import { login } from "../api/admin";

export default function LoginPanel({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const result = await login(username, password);
      onLoginSuccess(result.access_token, result.role);
    } catch (err) {
      setError("Kullanıcı adı veya parola hatalı");
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-slate-900 p-8 rounded-xl w-80 space-y-4">
        <h1 className="text-xl font-bold text-cyan-400">Vanguard Sentinel</h1>
        <input
          className="w-full bg-slate-800 text-slate-100 p-2 rounded"
          placeholder="Kullanıcı adı"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="w-full bg-slate-800 text-slate-100 p-2 rounded"
          type="password"
          placeholder="Parola"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button className="w-full bg-cyan-600 hover:bg-cyan-500 text-white p-2 rounded" type="submit">
          Giriş Yap
        </button>
      </form>
    </div>
  );
}
