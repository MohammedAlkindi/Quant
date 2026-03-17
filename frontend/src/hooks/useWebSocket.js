import { useEffect, useRef, useState } from 'react';

export default function useWebSocket(url) {
  const socketRef = useRef(null);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    if (!url) return undefined;
    socketRef.current = new WebSocket(url);
    socketRef.current.onmessage = (event) => {
      setMessages((prev) => [...prev.slice(-99), JSON.parse(event.data)]);
    };
    return () => socketRef.current?.close();
  }, [url]);

  return messages;
}
