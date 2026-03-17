export default function Portfolio({ portfolio }) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <h3 className="font-semibold">Portfolio</h3>
      <p className="text-sm">Equity: ${portfolio.equity?.toFixed?.(2) || 0}</p>
      <p className="mb-2 text-sm">Cash: ${portfolio.cash?.toFixed?.(2) || 0}</p>
      <table className="w-full text-left text-sm">
        <thead><tr><th>Ticker</th><th>Qty</th><th>P&L</th></tr></thead>
        <tbody>
          {portfolio.positions?.map((p) => (
            <tr key={p.ticker}><td>{p.ticker}</td><td>{p.qty}</td><td>{p.unrealized_pl?.toFixed?.(2)}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
