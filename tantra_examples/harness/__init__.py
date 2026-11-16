"""Application-layer harness for the examples learning path.

This package is the lightweight execution harness used by the numbered
examples: catalog loading, strategy manifests, the replay runner, event
logging, and the bar data service. It was renamed from the original
underscore-prefixed kernel package under root plan 0006 (T13) Thrust B; all
wheel domain models it once re-exported now come directly from the
``tantra`` wheel.
"""

from tantra_examples.harness.config import StrategyConfig
from tantra_examples.harness.loader import (
    CATALOG_DIRNAME,
    CATALOG_ENV,
    CatalogError,
    CatalogRegistryEntry,
    CatalogStrategy,
    StrategyVersionInfo,
    find_catalog,
    load_catalog_strategy,
    load_named,
    load_strategy,
    resolve_strategy_version,
)
from tantra_examples.harness.log import EventFilter, register_event, setup_event_logging
from tantra_examples.harness.manifest import (
    STRATEGY_API_VERSION,
    ManifestError,
    ParameterSpec,
    StrategyManifest,
    Subscriptions,
    TimeframeSpec,
    Universe,
    WarmupBars,
    param_range_to_schema,
    sweep_space_from_manifest,
    trial_grid_from_manifest,
)
from tantra_examples.harness.ports import BarStore, MarketDataProvider, validate_bar
from tantra_examples.harness.runner import (
    ExecutionPort,
    ExecutionPortLike,
    IntentRejection,
    OrderRejection,
    RunResult,
    StrategyRunner,
    SubmittedIntent,
    SuppressedIntent,
)
from tantra_examples.harness.service import DataService
from tantra_examples.harness.testing import ReplayResult, replay

__all__ = [
    # loader
    "CATALOG_DIRNAME",
    "CATALOG_ENV",
    # manifest
    "STRATEGY_API_VERSION",
    # ports
    "BarStore",
    "CatalogError",
    "CatalogRegistryEntry",
    "CatalogStrategy",
    # service
    "DataService",
    # log
    "EventFilter",
    # runner
    "ExecutionPort",
    "ExecutionPortLike",
    "IntentRejection",
    "ManifestError",
    "MarketDataProvider",
    "OrderRejection",
    "ParameterSpec",
    # testing
    "ReplayResult",
    "RunResult",
    # config
    "StrategyConfig",
    "StrategyManifest",
    "StrategyRunner",
    "StrategyVersionInfo",
    "SubmittedIntent",
    "Subscriptions",
    "SuppressedIntent",
    "TimeframeSpec",
    "Universe",
    "WarmupBars",
    "find_catalog",
    "load_catalog_strategy",
    "load_named",
    "load_strategy",
    "param_range_to_schema",
    "register_event",
    "replay",
    "resolve_strategy_version",
    "setup_event_logging",
    "sweep_space_from_manifest",
    "trial_grid_from_manifest",
    "validate_bar",
]
