import { useEffect, useState } from 'react';
import client from '../api/client';
import AnomalyBadge from '../components/AnomalyBadge';
import ClaudeChat from '../components/ClaudeChat';
import Portfolio from '../components/Portfolio';
import PriceChart from '../components/PriceChart';
import SentimentBar from '../components/SentimentBar';
import SignalCard from '../components/SignalCard';
import TradePanel from '../components/TradePanel';
import usePortfolio from '../hooks/usePortfolio';
import useSignal from '../hooks/useSignal';

export default function Dashboard() {
  const [ticker] = useState('AAPL');
  const [history, setHistory] = useState([]);
  const signal = useSignal(ticker);
  const portfolio = usePortfolio();

  useEffect(() => {
    client.get(`/history/${ticker}`).then((res) => setHistory(res.data));
  }, [ticker]);

  return (
    <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <PriceChart data={history} />
        <div className="grid grid-cols-2 gap-4">
          <SignalCard signal={signal} />
          <SentimentBar value={signal?.sentiment_score || 0} />
        </div>
        <div><AnomalyBadge anomaly={signal?.anomaly_flags} /></div>
        <ClaudeChat context={signal || { ticker }} />
      </div>
      <div className="space-y-4">
        <TradePanel ticker={ticker} />
        <Portfolio portfolio={portfolio} />
      </div>
    </div>
  );
}
