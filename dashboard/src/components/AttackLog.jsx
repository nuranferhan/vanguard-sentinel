const ACTION_COLORS = {
  allowed: "text-emerald-400",
  rate_limited: "text-amber-400",
  blacklisted: "text-red-500",
  anomaly_blocked: "text-fuchsia-400",
  auth_failed: "text-orange-400",
  replay_blocked: "text-purple-400",
  geo_blocked: "text-sky-400",
  mtls_rejected: "text-rose-400",
  cheat_detected: "text-pink-400",
};

export default function AttackLog({ events }) {
  return (
    <div className="bg-slate-900 rounded-xl p-4 shadow-lg h-[320px] overflow-y-auto">
      <h2 className="text-slate-200 font-semibold mb-3">Engellenen Saldırılar</h2>
      <ul className="space-y-1 font-mono text-sm">
        {events.filter((e) => e.action !== "allowed").map((e, i) => (
          <li key={i} className="flex justify-between border-b border-slate-800 py-1">
            <span className="text-slate-400">{e.client_ip}</span>
            <span className={ACTION_COLORS[e.action] || "text-slate-300"}>{e.action}</span>
            <span className="text-slate-500">{e.endpoint}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
