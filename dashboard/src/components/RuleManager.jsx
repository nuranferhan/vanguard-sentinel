import { useEffect, useState } from "react";
import { getRules, createRule } from "../api/admin";

export default function RuleManager({ token, role }) {
  const [rules, setRules] = useState([]);
  const [name, setName] = useState("");
  const [pattern, setPattern] = useState("");
  const [limit, setLimit] = useState("");

  async function refresh() {
    const data = await getRules(token);
    setRules(data);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate() {
    await createRule(token, { name, endpoint_pattern: pattern, max_requests_per_sec: limit });
    setName("");
    setPattern("");
    setLimit("");
    refresh();
  }

  if (role !== "admin") {
    return (
      <div className="bg-slate-900 rounded-xl p-4 shadow-lg text-slate-500 text-sm">
        Kural yönetimi yalnızca admin rolüne açıktır.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-xl p-4 shadow-lg space-y-3">
      <h2 className="text-slate-200 font-semibold">Manuel Filtre Kuralları</h2>
      <div className="flex gap-2">
        <input
          className="bg-slate-800 text-slate-100 p-2 rounded flex-1"
          placeholder="Kural adı"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="bg-slate-800 text-slate-100 p-2 rounded flex-1"
          placeholder="Endpoint deseni (/player/*)"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
        />
        <input
          className="bg-slate-800 text-slate-100 p-2 rounded w-32"
          placeholder="Limit/sn"
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
        />
        <button className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 rounded" onClick={handleCreate}>
          Ekle
        </button>
      </div>
      <ul className="text-sm font-mono space-y-1">
        {rules.map((rule) => (
          <li key={rule.rule_id} className="text-slate-400 flex justify-between border-b border-slate-800 py-1">
            <span>{rule.name}</span>
            <span>{rule.endpoint_pattern}</span>
            <span>{rule.max_requests_per_sec ?? "-"}/sn</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
