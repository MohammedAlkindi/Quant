"""Cost-aware daily backtest engine.

Execution model, stated precisely so the tests can hold it to account:

- A target weight decided on bar t's close fills at bar t+1's OPEN. Nothing
  ever trades on the bar whose close produced the signal, so the engine
  cannot look ahead. The decision on the final bar never executes.
- One-way drag = commission + half bid-ask spread + slippage, in bps of the
  fill. Buys fill at open*(1+drag) and are sized against that fill so cash
  cannot go negative; sells are sized against the raw open (so a full exit
  sells exactly the position) and receive open*(1-drag).
- The engine trades only when the target weight changes. It does not
  continuously rebalance positions that drift from their target.
- Long-only, unlevered: weights must lie in [0, 1]. Fractional shares.
- Equity is marked at each bar's close.
"""

from dataclasses import dataclass

import pandas as pd

TARGET_EPSILON = 1e-12
TRADE_COLUMNS = ['date', 'side', 'shares', 'fill_price', 'notional', 'cost']


@dataclass(frozen=True)
class CostModel:
    commission_bps: float = 0.5
    half_spread_bps: float = 0.5
    slippage_bps: float = 1.0

    @property
    def one_way_drag(self) -> float:
        return (self.commission_bps + self.half_spread_bps + self.slippage_bps) / 1e4


@dataclass
class BacktestResult:
    equity: pd.Series
    returns: pd.Series
    trades: pd.DataFrame
    traded_notional: float
    total_costs: float
    final_equity: float


def _validate(prices: pd.DataFrame, target_weights: pd.Series) -> None:
    for col in ('open', 'close'):
        if col not in prices.columns:
            raise ValueError(f'prices must have an {col!r} column')
        if prices[col].isna().any() or (prices[col] <= 0).any():
            raise ValueError(f'prices[{col!r}] must be positive and free of NaN')
    if not prices.index.is_monotonic_increasing:
        raise ValueError('prices index must be sorted ascending')
    if not target_weights.index.equals(prices.index):
        raise ValueError('target_weights must share the prices index')
    if target_weights.isna().any():
        raise ValueError('target_weights must not contain NaN')
    if (target_weights < 0).any() or (target_weights > 1).any():
        raise ValueError('target_weights must lie in [0, 1]: long-only, unlevered')


def run_backtest(
    prices: pd.DataFrame,
    target_weights: pd.Series,
    costs: CostModel,
    initial_cash: float = 100_000.0,
) -> BacktestResult:
    _validate(prices, target_weights)
    drag = costs.one_way_drag

    cash = float(initial_cash)
    shares = 0.0
    applied_target = 0.0
    pending_target: float | None = None
    equity_values: list[float] = []
    trades: list[dict] = []
    traded_notional = 0.0
    total_costs = 0.0

    opens = prices['open'].to_numpy()
    closes = prices['close'].to_numpy()
    weights = target_weights.to_numpy()

    for i, date in enumerate(prices.index):
        if pending_target is not None:
            open_price = opens[i]
            equity_at_open = cash + shares * open_price
            delta_value = pending_target * equity_at_open - shares * open_price
            if abs(delta_value) > TARGET_EPSILON * max(equity_at_open, 1.0):
                if delta_value > 0:
                    fill_price = open_price * (1 + drag)
                    shares_delta = delta_value / fill_price
                else:
                    fill_price = open_price * (1 - drag)
                    shares_delta = delta_value / open_price
                cash -= shares_delta * fill_price
                notional = abs(shares_delta) * open_price
                cost = notional * drag
                traded_notional += notional
                total_costs += cost
                shares += shares_delta
                trades.append(
                    {
                        'date': date,
                        'side': 'buy' if shares_delta > 0 else 'sell',
                        'shares': abs(shares_delta),
                        'fill_price': fill_price,
                        'notional': notional,
                        'cost': cost,
                    }
                )
            applied_target = pending_target
            pending_target = None

        equity_values.append(cash + shares * closes[i])

        if abs(weights[i] - applied_target) > TARGET_EPSILON:
            pending_target = float(weights[i])

    equity = pd.Series(equity_values, index=prices.index, name='equity')
    returns = equity.pct_change().dropna()
    trades_frame = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    return BacktestResult(
        equity=equity,
        returns=returns,
        trades=trades_frame,
        traded_notional=traded_notional,
        total_costs=total_costs,
        final_equity=float(equity.iloc[-1]),
    )
