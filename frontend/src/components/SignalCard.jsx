export default function SignalCard({ signal }) {
  if (!signal) return null;
  const color = signal.recommendation === 'BUY' ? 'text-emerald-600' : signal.recommendation === 'SELL' ? 'text-red-600' : 'text-amber-500';
  return (
    <div className="rounded-lg border bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-500">Signal</h3>
      <p className={`text-2xl font-bold ${color}`}>{signal.recommendation}</p>
      <p className="text-sm text-slate-600">Confidence: {(signal.confidence * 100).toFixed(1)}%</p>
    </div>
  );
}
