from backend.config import get_settings
from backend.data.alpha_vantage import fetch_news


def get_headlines(ticker: str) -> list[str]:
    settings = get_settings()
    if not settings.alpha_vantage_api_key:
        return []
    feed = fetch_news(settings.alpha_vantage_api_key, ticker, limit=20)
    return [item.get('title', '') for item in feed]
