import numpy as np

from ml.sentiment.finbert import score_headlines
from ml.sentiment.news_scraper import get_headlines


def aggregate_sentiment(ticker: str) -> float:
    headlines = get_headlines(ticker)
    scores = score_headlines(headlines)
    return float(np.clip(np.mean(scores), -1, 1))
