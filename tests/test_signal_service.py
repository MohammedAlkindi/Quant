"""Tests for the live heuristic signal (backend.services.signal_service).

These exercise the real components where they are deterministic (no Alpha
Vantage key -> sentiment 0.0 without loading FinBERT; no PPO checkpoint ->
rl_action 'hold'; IsolationForest is seeded) and monkeypatch them only to
verify the documented blend weights and thresholds.
"""

import numpy as np
import pytest

import backend.services.signal_service as signal_module
from backend.config import get_settings
from backend.services.signal_service import SignalService


@pytest.fixture(autouse=True)
def keyless_settings(monkeypatch):
    monkeypatch.setenv('POSTGRES_URL', 'postgresql+psycopg://quant:quant@localhost:5432/quant')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
    monkeypatch.delenv('ALPHA_VANTAGE_API_KEY', raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_candles(closes):
    return [{'close': float(c)} for c in closes]


def test_insufficient_data_returns_hold():
    result = SignalService().predict('SPY', make_candles([100.0]))
    assert result == {'ticker': 'SPY', 'recommendation': 'HOLD', 'confidence': 0.5, 'reason': 'insufficient-data'}


def test_momentum_projection_is_plain_arithmetic_not_a_model():
    # close[-5] = 100, close[-1] = 120 -> momentum 0.2 -> 120 * (1 + 0.2*0.2) = 124.8
    result = SignalService().predict('SPY', make_candles([100.0] * 59 + [120.0]))
    assert result['momentum_projection'] == pytest.approx(124.8, rel=1e-5)


def test_quiet_tape_defaults_to_hold_at_floor_confidence():
    closes = np.linspace(100.0, 101.0, 60)  # ~0.07% 4-session momentum
    result = SignalService().predict('SPY', make_candles(closes))
    assert result['recommendation'] == 'HOLD'
    assert result['confidence'] == 0.5
    assert result['sentiment_score'] == 0.0  # keyless: no headlines, FinBERT never loads
    assert result['rl_action'] == 'hold'    # no checkpoint shipped


def test_price_spike_flags_anomaly_and_blocks_the_buy_it_caused():
    # +100% jump: raw score 0.4*tanh(3) = 0.398 would be a BUY, but the same
    # jump z-flags as an anomaly, halving the score below the 0.2 threshold.
    result = SignalService().predict('SPY', make_candles([100.0] * 59 + [200.0]))
    assert result['anomaly_flags']['is_anomaly'] is True
    assert result['anomaly_flags']['z_score'] > 2.5
    assert result['recommendation'] == 'HOLD'


def test_blend_weights_and_buy_threshold(monkeypatch):
    monkeypatch.setattr(signal_module, 'aggregate_sentiment', lambda ticker: 1.0)
    monkeypatch.setattr(signal_module, 'get_rl_action', lambda prices: 'buy')
    monkeypatch.setattr(
        signal_module, 'detect_anomaly', lambda series: {'is_anomaly': False, 'z_score': 0.0, 'model_flag': 1}
    )
    result = SignalService().predict('SPY', make_candles([100.0] * 60))
    # momentum 0 -> score = 0.3*sentiment + 0.3*rl = 0.6
    assert result['recommendation'] == 'BUY'
    assert result['confidence'] == pytest.approx(0.6)


def test_blend_weights_and_sell_threshold(monkeypatch):
    monkeypatch.setattr(signal_module, 'aggregate_sentiment', lambda ticker: -1.0)
    monkeypatch.setattr(signal_module, 'get_rl_action', lambda prices: 'sell')
    monkeypatch.setattr(
        signal_module, 'detect_anomaly', lambda series: {'is_anomaly': False, 'z_score': 0.0, 'model_flag': 1}
    )
    result = SignalService().predict('SPY', make_candles([100.0] * 60))
    assert result['recommendation'] == 'SELL'
    assert result['confidence'] == pytest.approx(0.6)
