from polygon import RESTClient


class PolygonClient:
    def __init__(self, api_key: str):
        self.client = RESTClient(api_key=api_key)

    def get_last_trade(self, ticker: str) -> dict:
        trade = self.client.get_last_trade(ticker)
        return {'ticker': ticker, 'price': trade.price, 'timestamp': trade.sip_timestamp}

    def get_aggs(self, ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> list[dict]:
        aggs = self.client.get_aggs(ticker, multiplier=multiplier, timespan=timespan, from_=from_, to=to)
        return [a.__dict__ for a in aggs]
