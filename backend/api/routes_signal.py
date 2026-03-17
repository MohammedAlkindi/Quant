from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.market_service import MarketService
from backend.services.signal_service import SignalService

router = APIRouter(tags=['signals'])
market_service = MarketService()
signal_service = SignalService()


class PredictRequest(BaseModel):
    ticker: str


@router.post('/signal/predict')
def predict(req: PredictRequest):
    candles = market_service.get_history(req.ticker.upper(), period='3mo', interval='1d')
    return signal_service.predict(req.ticker.upper(), candles)


@router.get('/anomaly/{ticker}')
def anomaly(ticker: str):
    candles = market_service.get_history(ticker.upper(), period='3mo', interval='1d')
    payload = signal_service.predict(ticker.upper(), candles)
    return payload['anomaly_flags']
