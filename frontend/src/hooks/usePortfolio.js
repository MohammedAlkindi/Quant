import { useEffect, useState } from 'react';
import client from '../api/client';

export default function usePortfolio() {
  const [portfolio, setPortfolio] = useState({ equity: 0, cash: 0, positions: [] });
  useEffect(() => {
    client.get('/portfolio').then((res) => setPortfolio(res.data));
  }, []);
  return portfolio;
}
