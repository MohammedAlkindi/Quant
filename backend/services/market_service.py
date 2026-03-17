from datetime import date, timedelta

from backend.config import get_settings
from backend.data.alpha_vantage import fetch_fundamentals
from backend.data.cache import RedisCache
from backend.data.polygon import PolygonClient
from backend.data.yfinance import fetch_history


class MarketService:
    def __init__(self):
        settings = get_settings()
        self.settings = settings
        self.cache = RedisCache(settings.redis_url)
        self.polygon = PolygonClient(settings.polygon_api_key) if settings.polygon_api_key else None

    def get_quote(self, ticker: str) -> dict:
        cache_key = f'quote:{ticker}'
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        if self.polygon:
            quote = self.polygon.get_last_trade(ticker)
        else:
            hist = fetch_history(ticker, period='5d', interval='1d')
            latest = hist[-1] if hist else {'close': 0.0, 'timestamp': ''}
            quote = {'ticker': ticker, 'price': latest['close'], 'timestamp': latest['timestamp']}
        self.cache.set(cache_key, quote, ttl=5)
        return quote

    def get_history(self, ticker: str, period: str = '6mo', interval: str = '1d') -> list[dict]:
        return fetch_history(ticker, period=period, interval=interval)

    def get_prices(self, ticker: str) -> dict:
        to_date = date.today()
        from_date = to_date - timedelta(days=30)
        if self.polygon:
            candles = self.polygon.get_aggs(ticker, 1, 'day', from_date.isoformat(), to_date.isoformat())
        else:
            candles = self.get_history(ticker, period='1mo', interval='1d')
        fundamentals = fetch_fundamentals(self.settings.alpha_vantage_api_key, ticker) if self.settings.alpha_vantage_api_key else {}
        return {'ticker': ticker, 'candles': candles, 'fundamentals': fundamentals}
