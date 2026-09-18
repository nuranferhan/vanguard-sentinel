export default function ServerHealth({ health }) {
  if (!health) return null;
  return (
    <div className="bg-slate-900 rounded-xl p-4 shadow-lg grid grid-cols-3 gap-4">
      <Metric label="CPU Kullanımı" value={`${health.cpu_usage_percent.toFixed(1)}%`} />
      <Metric label="Aktif Bağlantı" value={health.active_connections} />
      <Metric label="Son 1 Dakikada Engellenen" value={health.blocked_last_minute} />
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <p className="text-slate-500 text-xs">{label}</p>
      <p className="text-slate-100 text-xl font-bold">{value}</p>
    </div>
  );
}
