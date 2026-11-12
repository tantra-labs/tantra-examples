"""Composable portfolio construction: universe, selection, weighting, schedule.

``PortfolioStrategy(universe, weighting, schedule, selector)`` wires the parts into a
``TargetWeightStrategy``. Each part is a small ``Protocol`` with simple implementations.
"""
# mirror: kernel-verbatim port (gap 0006)

from tantra_examples._kernel.portfolio_strategy.factory import build_portfolio_strategy
from tantra_examples._kernel.portfolio_strategy.schedule import (
    AnyOf,
    DriftBand,
    EveryNDays,
    MonthlyFirstSession,
    RebalanceSchedule,
    ScheduleState,
)
from tantra_examples._kernel.portfolio_strategy.scoring import (
    low_volatility,
    mean_reversion,
    momentum,
)
from tantra_examples._kernel.portfolio_strategy.selection import SelectAll, Selector, TopN
from tantra_examples._kernel.portfolio_strategy.strategy import PortfolioStrategy
from tantra_examples._kernel.portfolio_strategy.universe import (
    NamedUniverse,
    StaticUniverse,
    Universe,
)
from tantra_examples._kernel.portfolio_strategy.view import MarketView, PriceHistory
from tantra_examples._kernel.portfolio_strategy.weighting import (
    EqualWeight,
    InverseVolatility,
    WeightingScheme,
)

__all__ = [
    "AnyOf",
    "DriftBand",
    "EqualWeight",
    "EveryNDays",
    "InverseVolatility",
    "MarketView",
    "MonthlyFirstSession",
    "NamedUniverse",
    "PortfolioStrategy",
    "PriceHistory",
    "RebalanceSchedule",
    "ScheduleState",
    "SelectAll",
    "Selector",
    "StaticUniverse",
    "TopN",
    "Universe",
    "WeightingScheme",
    "build_portfolio_strategy",
    "low_volatility",
    "mean_reversion",
    "momentum",
]
