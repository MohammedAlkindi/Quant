import numpy as np

from ml.anomaly.detector import detect_anomaly
from ml.rl.agent import get_rl_action
from ml.sentiment.aggregator import aggregate_sentiment


class SignalService:
    def predict(self, ticker: str, candles: list[dict]) -> dict:
        close_series = np.array([c.get('close') or c.get('Close') for c in candles], dtype=np.float32)
        if len(close_series) < 2:
            return {'ticker': ticker, 'recommendation': 'HOLD', 'confidence': 0.5, 'reason': 'insufficient-data'}
        momentum = (close_series[-1] - close_series[-5]) / max(close_series[-5], 1e-6) if len(close_series) >= 5 else 0.0
        lstm_prediction = float(close_series[-1] * (1 + momentum * 0.2))
        rl_action = get_rl_action(close_series)
        anomaly = detect_anomaly(close_series.tolist())
        sentiment = aggregate_sentiment(ticker)

        score = 0.4 * np.tanh(momentum * 3) + 0.3 * sentiment + 0.3 * (1 if rl_action == 'buy' else -1 if rl_action == 'sell' else 0)
        if anomaly['is_anomaly']:
            score *= 0.5

        recommendation = 'BUY' if score > 0.2 else 'SELL' if score < -0.2 else 'HOLD'
        confidence = float(min(0.99, max(0.5, abs(score))))

        return {
            'ticker': ticker,
            'lstm_prediction': lstm_prediction,
            'rl_action': rl_action,
            'anomaly_flags': anomaly,
            'sentiment_score': sentiment,
            'recommendation': recommendation,
            'confidence': confidence,
        }
