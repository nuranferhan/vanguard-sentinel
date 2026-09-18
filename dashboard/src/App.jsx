import { useEffect, useState } from "react";
import { connectStatsSocket } from "./api/ws";
import TrafficChart from "./components/TrafficChart";
import AttackLog from "./components/AttackLog";
import ServerHealth from "./components/ServerHealth";
import LoginPanel from "./components/LoginPanel";
import RuleManager from "./components/RuleManager";

export default function App() {
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);
  const [events, setEvents] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const socket = connectStatsSocket(
      (event) => {
        setEvents((prev) => [event, ...prev].slice(0, 200));
        setChartData((prev) =>
          [
            ...prev,
            {
              time: new Date(event.timestamp * 1000).toLocaleTimeString(),
              requestsPerSecond: event.requests_last_window,
            },
          ].slice(-30)
        );
      },
      (healthData) => setHealth(healthData)
    );
    return () => socket.close();
  }, []);

  if (!token) {
    return (
      <LoginPanel
        onLoginSuccess={(newToken, newRole) => {
          setToken(newToken);
          setRole(newRole);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-cyan-400">Vanguard Sentinel — Güvenlik Paneli</h1>
        <span className="text-slate-400 text-sm">Rol: {role}</span>
      </div>
      <ServerHealth health={health} />
      <TrafficChart data={chartData} />
      <RuleManager token={token} role={role} />
      <AttackLog events={events} />
    </div>
  );
}
