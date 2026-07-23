import pandas as pd
import pandas_ta as ta


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['rsi'] = ta.rsi(out['close'], length=14)
    macd = ta.macd(out['close'])
    out['macd'] = macd['MACD_12_26_9']
    bb = ta.bbands(out['close'])
    out['bb_low'] = bb['BBL_5_2.0']
    out['bb_high'] = bb['BBU_5_2.0']
    return out.dropna()
