"""Portfolio math as pure functions. No I/O, no state, no randomness."""

import numpy as np
import pandas as pd


def total_return(equity: pd.Series) -> float:
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def cagr(equity: pd.Series, periods_per_year: int = 252) -> float:
    n_periods = len(equity) - 1
    if n_periods <= 0:
        return 0.0
    growth = equity.iloc[-1] / equity.iloc[0]
    return float(growth ** (periods_per_year / n_periods) - 1.0)


def sharpe(returns: pd.Series, periods_per_year: int = 252, rf_annual: float = 0.0) -> float:
    """Annualized Sharpe ratio with sample std (ddof=1). Zero-variance series map to 0.0."""
    if len(returns) < 2:
        return 0.0
    excess = returns - rf_annual / periods_per_year
    std = float(excess.std(ddof=1))
    if std == 0.0 or np.isnan(std):
        return 0.0
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> float:
    """Worst peak-to-trough decline as a negative fraction (0.0 if equity never falls)."""
    running_peak = equity.cummax()
    return float((equity / running_peak - 1.0).min())


def annual_turnover(traded_notional: float, avg_equity: float, n_periods: int, periods_per_year: int = 252) -> float:
    """Absolute traded notional per year, as a multiple of average equity."""
    if avg_equity <= 0 or n_periods <= 0:
        return 0.0
    years = n_periods / periods_per_year
    return float(traded_notional / avg_equity / years)
