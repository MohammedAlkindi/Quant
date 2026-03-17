from datetime import datetime
import yfinance as yf


def fetch_history(ticker: str, period: str = '6mo', interval: str = '1d') -> list[dict]:
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        return []
    rows = []
    for idx, row in df.iterrows():
        rows.append({
            'timestamp': idx.isoformat() if isinstance(idx, datetime) else str(idx),
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': float(row['Volume']),
        })
    return rows
