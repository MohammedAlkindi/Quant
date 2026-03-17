from fastapi import APIRouter, Query

from backend.services.market_service import MarketService

router = APIRouter(tags=['market'])
service = MarketService()


@router.get('/prices/{ticker}')
def prices(ticker: str):
    return service.get_prices(ticker.upper())


@router.get('/quote/{ticker}')
def quote(ticker: str):
    return service.get_quote(ticker.upper())


@router.get('/history/{ticker}')
def history(ticker: str, period: str = Query('6mo'), interval: str = Query('1d')):
    return service.get_history(ticker.upper(), period=period, interval=interval)
