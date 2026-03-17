import requests

BASE_URL = 'https://www.alphavantage.co/query'


def fetch_fundamentals(api_key: str, ticker: str) -> dict:
    params = {'function': 'OVERVIEW', 'symbol': ticker, 'apikey': api_key}
    return requests.get(BASE_URL, params=params, timeout=20).json()


def fetch_news(api_key: str, ticker: str, limit: int = 20) -> list[dict]:
    params = {'function': 'NEWS_SENTIMENT', 'tickers': ticker, 'apikey': api_key, 'limit': limit}
    data = requests.get(BASE_URL, params=params, timeout=20).json()
    return data.get('feed', [])
