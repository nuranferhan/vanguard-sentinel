import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function TrafficChart({ data }) {
  return (
    <div className="bg-slate-900 rounded-xl p-4 shadow-lg">
      <h2 className="text-slate-200 font-semibold mb-3">Canlı İstek Trafiği</h2>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="time" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip contentStyle={{ background: "#0f172a", border: "none" }} />
          <Line type="monotone" dataKey="requestsPerSecond" stroke="#22d3ee" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
