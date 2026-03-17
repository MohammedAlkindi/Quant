import { useState } from 'react';
import client from '../api/client';

export default function TradePanel({ ticker }) {
  const [side, setSide] = useState('buy');
  const [qty, setQty] = useState(1);
  const [status, setStatus] = useState('');

  const execute = async () => {
    const { data } = await client.post('/trade/execute', { ticker, side, qty: Number(qty), confirmed: true });
    setStatus(data.status);
  };

  return (
    <div className="rounded-lg border bg-white p-4">
      <h3 className="mb-3 font-semibold">Trade Execution</h3>
      <div className="flex gap-2">
        <select className="rounded border px-2" value={side} onChange={(e) => setSide(e.target.value)}>
          <option value="buy">Buy</option>
          <option value="sell">Sell</option>
        </select>
        <input className="w-20 rounded border px-2" type="number" value={qty} min="1" onChange={(e) => setQty(e.target.value)} />
        <button className="rounded bg-blue-600 px-3 py-1 text-white" onClick={execute}>Confirm</button>
      </div>
      {status && <p className="mt-2 text-sm">Order: {status}</p>}
    </div>
  );
}
