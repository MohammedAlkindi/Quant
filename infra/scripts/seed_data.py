from pathlib import Path
import json

from backend.config import get_settings
from backend.data.yfinance import fetch_history


if __name__ == '__main__':
    settings = get_settings()
    tickers = [t.strip() for t in settings.default_tickers.split(',') if t.strip()]
    out_dir = Path('data_seed')
    out_dir.mkdir(exist_ok=True)
    for ticker in tickers:
        data = fetch_history(ticker, period='2y', interval='1d')
        (out_dir / f'{ticker}.json').write_text(json.dumps(data))
        print(f'Seeded {ticker}: {len(data)} rows')
