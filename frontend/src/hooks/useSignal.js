import { useEffect, useState } from 'react';
import client from '../api/client';

export default function useSignal(ticker) {
  const [signal, setSignal] = useState(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      const { data } = await client.post('/signal/predict', { ticker });
      if (active) setSignal(data);
    };
    load();
    const id = setInterval(load, 60000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [ticker]);

  return signal;
}
