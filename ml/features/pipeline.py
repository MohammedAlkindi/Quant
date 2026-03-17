import pandas as pd

from ml.features.technical import add_technical_features


def build_feature_matrix(candles: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(candles)
    rename_map = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}
    df = df.rename(columns=rename_map)
    cols = ['open', 'high', 'low', 'close', 'volume']
    df = df[[c for c in cols if c in df.columns]]
    return add_technical_features(df)
