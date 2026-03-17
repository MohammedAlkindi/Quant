export default function SentimentBar({ value = 0 }) {
  const pct = Math.min(100, Math.max(0, (value + 1) * 50));
  return (
    <div className="rounded-lg border bg-white p-4">
      <h3 className="mb-2 text-sm font-semibold">Sentiment</h3>
      <div className="h-3 w-full rounded bg-slate-200">
        <div className="h-3 rounded bg-indigo-500" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-1 text-xs text-slate-500">{value.toFixed(2)}</p>
    </div>
  );
}
