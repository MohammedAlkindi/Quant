import { useState } from 'react';
import client from '../api/client';

export default function Research() {
  const [ticker, setTicker] = useState('AAPL');
  const [result, setResult] = useState(null);
  const run = async () => {
    const { data } = await client.post('/signal/predict', { ticker });
    setResult(data);
  };
  return (
    <div className="p-4">
      <h1 className="mb-2 text-xl font-bold">Research</h1>
      <div className="mb-3 flex gap-2">
        <input className="rounded border px-2" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} />
        <button className="rounded bg-blue-600 px-3 py-1 text-white" onClick={run}>Run Backtest Proxy</button>
      </div>
      <pre className="rounded border bg-white p-2 text-sm">{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}
