export default function AnomalyBadge({ anomaly }) {
  const state = anomaly?.is_anomaly ? 'HIGH RISK' : 'NORMAL';
  const cls = anomaly?.is_anomaly ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700';
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${cls}`}>{state}</span>;
}
