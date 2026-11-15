"""ai_research/05_rl_training: design notes for reinforcement-learning training.

This is a design-documentation script: it prints the design notes below and the
optional-dependency requirement. torch and gymnasium are optional extras and are never
imported by this script or anywhere in the default install. ``tantra.ai.rl.*`` does not
ship in the wheel.

Run::

    python examples/ai_research/05_rl_training.py

Pitfalls::

    - Train/test leakage: split by time, never shuffle episodes across the split, fit feature
      scaling on the training period only, and score on a later period that was never used to pick
      hyperparameters or a checkpoint.
    - Reward hacking: an agent maximises the reward as the simulator computes it. With same-bar
      fills, no impact or free leverage it will learn those artifacts. Put costs and risk
      in the reward and inspect the learned actions, not just the final equity.
    - Overfitting one path: a policy trained on a single price path, synthetic or real, can
      memorise it. Train on many paths, and report the spread across several seeds and regimes,
      not the best run.
    - Synthetic data says nothing about markets: a policy that beats a random-walk environment has
      learned the generator, and one that wins on it proves no edge.
    - Non-stationarity: a policy fit to one regime or to today's survivors can fail when the
      universe or volatility changes. Walk forward and re-test on a point-in-time universe.
"""

from __future__ import annotations

import sys

__all__ = ["DESIGN_NOTES", "main"]

DESIGN_NOTES = (
    "Reinforcement-learning training for trading strategies is documented design, not a shipped "
    "surface: tantra.ai.rl.* does not exist in the wheel. When it ships, the trainer must run "
    "against an offline simulator (the same Decimal bars as the backtester), keep torch and "
    "gymnasium as optional extras, and defend against every pitfall above. A trainer on live "
    "data with a learned reward is a strategy that must still pass the same risk gate and "
    "replayable-journal discipline as any other."
)


def main(argv: list[str] | None = None) -> int:
    print(__doc__)
    print()
    print(DESIGN_NOTES)
    print()
    print(
        "Dependency requirement: torch and gymnasium are optional extras and are NOT imported "
        "by this script or its tests."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
