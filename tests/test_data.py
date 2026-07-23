import pandas as pd
import pytest

from quant.data import load_ohlcv

CSV = """date,open,high,low,close,volume
2024-01-03,102,103,101,102.5,3000
2024-01-02,100,101,99,100.5,2000
2024-01-04,103,104,102,103.5,4000
"""


def write_csv(tmp_path, text):
    path = tmp_path / 'prices.csv'
    path.write_text(text)
    return path


def test_load_ohlcv_parses_sorts_and_indexes_by_date(tmp_path):
    df = load_ohlcv(write_csv(tmp_path, CSV))
    assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
    assert df.index.tolist() == [pd.Timestamp('2024-01-02'), pd.Timestamp('2024-01-03'), pd.Timestamp('2024-01-04')]
    assert df.loc[pd.Timestamp('2024-01-02'), 'close'] == 100.5


def test_load_ohlcv_rejects_duplicate_dates(tmp_path):
    text = CSV + '2024-01-03,1,1,1,1,1\n'
    with pytest.raises(ValueError, match='duplicate'):
        load_ohlcv(write_csv(tmp_path, text))


def test_load_ohlcv_rejects_nonpositive_prices(tmp_path):
    text = 'date,open,high,low,close,volume\n2024-01-02,100,101,99,0,2000\n'
    with pytest.raises(ValueError, match='positive'):
        load_ohlcv(write_csv(tmp_path, text))


def test_load_ohlcv_rejects_missing_columns(tmp_path):
    text = 'date,open,close\n2024-01-02,100,101\n'
    with pytest.raises(ValueError, match='column'):
        load_ohlcv(write_csv(tmp_path, text))
