"""Fetch daily OHLCV history and write the vendored CSV used by quant.report.

Source: Yahoo Finance via yfinance, auto_adjust=True — prices are adjusted for
splits AND dividends, so buy-and-hold on `close` approximates total return.
The output is committed to the repo so backtests are reproducible offline;
re-running this script refreshes the snapshot (and will shift adjusted history
whenever new dividends have been paid).

Usage: python scripts/fetch_data.py [TICKER] [OUT_CSV]
Defaults: SPY data/SPY.csv
"""

import sys
from pathlib import Path

import yfinance as yf


def fetch(ticker: str, out_csv: Path) -> None:
    df = yf.Ticker(ticker).history(period='max', interval='1d', auto_adjust=True)
    if df.empty:
        raise SystemExit(f'no data returned for {ticker}')
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].rename(columns=str.lower)
    df.index = df.index.tz_localize(None).normalize()
    df.index.name = 'date'
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, float_format='%.6f')
    print(f'{ticker}: {len(df)} rows, {df.index[0].date()} -> {df.index[-1].date()}, written to {out_csv}')


if __name__ == '__main__':
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'SPY'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('data') / f'{ticker}.csv'
    fetch(ticker, out)
