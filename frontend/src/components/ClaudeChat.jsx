import { useState } from 'react';
import client from '../api/client';

export default function ClaudeChat({ context }) {
  const [answer, setAnswer] = useState('');
  const run = async () => {
    const { data } = await client.post('/explain', { context });
    setAnswer(data.raw);
  };
  return (
    <div className="rounded-lg border bg-white p-4">
      <button className="rounded bg-slate-800 px-3 py-1 text-white" onClick={run}>Ask Claude</button>
      <pre className="mt-2 whitespace-pre-wrap text-sm">{answer}</pre>
    </div>
  );
}
