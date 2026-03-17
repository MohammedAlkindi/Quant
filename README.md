# Quant — AI-Powered Personal Trading Assistant

Quant is a production-ready MVP for market data ingestion, signal generation, LLM-backed trade reasoning, and dashboard-based execution.

## Architecture
- **Data Layer**: Polygon + yfinance + Alpha Vantage with Redis caching.
- **ML/AI Layer**: LSTM/Transformer forecasting, anomaly detection, FinBERT sentiment, PPO RL.
- **LLM Layer**: Anthropic Claude (`claude-sonnet-4-20250514`) for explainable recommendations.
- **Dashboard**: React components for charting, signals, anomalies, sentiment, portfolio, and execution.

## Quickstart
1. Copy `.env.example` to `.env` and populate keys.
2. Start infra:
   ```bash
   cd infra && docker-compose up --build
   ```
3. Backend API: `http://localhost/api`
4. Frontend: `http://localhost`

## API Endpoints
- `GET /api/prices/{ticker}`
- `GET /api/quote/{ticker}`
- `GET /api/history/{ticker}`
- `POST /api/signal/predict`
- `GET /api/anomaly/{ticker}`
- `POST /api/trade/execute` (requires `confirmed=true`)
- `GET /api/portfolio`
- `POST /api/analyze`
- `POST /api/explain`

## Model & Training
- LSTM/Transformer consume 60-day rolling OHLCV + technical features.
- RL environment uses discrete actions and Sharpe-like reward.
- Checkpoints are saved to `ml/models/checkpoints/`.

## Dev scripts
- `python infra/scripts/seed_data.py`
- `python infra/scripts/train_lstm.py`
- `python infra/scripts/train_rl.py`
