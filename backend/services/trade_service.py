import alpaca_trade_api as tradeapi

from backend.config import get_settings


class TradeService:
    def __init__(self):
        # Constructed lazily: tradeapi.REST raises on empty keys, which must not block boot.
        self._client = None

    @property
    def client(self):
        if self._client is None:
            settings = get_settings()
            self._client = tradeapi.REST(settings.alpaca_api_key, settings.alpaca_secret_key, settings.alpaca_base_url)
        return self._client

    def execute_trade(self, ticker: str, side: str, qty: float, confirmed: bool, stop_loss_pct: float | None = 0.02) -> dict:
        if not confirmed:
            return {'status': 'rejected', 'reason': 'confirmation required'}

        order = self.client.submit_order(symbol=ticker, qty=qty, side=side.lower(), type='market', time_in_force='day')
        stop_loss = None
        if stop_loss_pct and side.lower() == 'buy':
            latest = float(self.client.get_latest_trade(ticker).price)
            stop_loss = round(latest * (1 - stop_loss_pct), 2)
        return {'status': 'submitted', 'order_id': order.id, 'stop_loss': stop_loss}

    def get_portfolio(self) -> dict:
        account = self.client.get_account()
        positions = [
            {'ticker': p.symbol, 'qty': float(p.qty), 'market_value': float(p.market_value), 'unrealized_pl': float(p.unrealized_pl)}
            for p in self.client.list_positions()
        ]
        return {'equity': float(account.equity), 'cash': float(account.cash), 'positions': positions}
