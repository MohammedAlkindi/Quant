import { useState } from 'react';

export default function Settings() {
  const [risk, setRisk] = useState(localStorage.getItem('risk_limit') || '0.02');
  const save = () => localStorage.setItem('risk_limit', risk);
  return (
    <div className="p-4">
      <h1 className="mb-3 text-xl font-bold">Settings</h1>
      <label className="block text-sm">Risk Limit</label>
      <input className="rounded border px-2" value={risk} onChange={(e) => setRisk(e.target.value)} />
      <button className="ml-2 rounded bg-slate-800 px-3 py-1 text-white" onClick={save}>Save</button>
    </div>
  );
}
