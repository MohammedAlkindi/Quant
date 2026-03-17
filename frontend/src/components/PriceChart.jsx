import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function PriceChart({ data }) {
  const chartData = data.map((d) => ({ time: d.timestamp?.slice(0, 10), close: d.close || d.c }));
  return (
    <div className="h-72 w-full rounded-lg border bg-white p-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <XAxis dataKey="time" />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Area type="monotone" dataKey="close" stroke="#2563eb" fill="#93c5fd" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
