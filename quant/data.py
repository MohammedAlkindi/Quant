"""Load vendored OHLCV CSVs. All I/O for the research package lives here."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'volume']


def load_ohlcv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in ['date', *REQUIRED_COLUMNS] if c not in df.columns]
    if missing:
        raise ValueError(f'missing column(s) {missing} in {path}')
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].duplicated().any():
        raise ValueError(f'duplicate dates in {path}')
    df = df.set_index('date').sort_index()[REQUIRED_COLUMNS].astype(float)
    price_cols = ['open', 'high', 'low', 'close']
    if df[price_cols].isna().any().any() or (df[price_cols] <= 0).any().any():
        raise ValueError(f'prices must be positive and free of NaN in {path}')
    return df
