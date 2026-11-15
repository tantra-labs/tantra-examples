# mirror: kernel-verbatim port (gap 0003: screener coverage surface) —
# Decimal-canonical wheel retarget (ex 0006): ``DateInterval`` is ``tantra.coverage``.

from __future__ import annotations

from tantra.coverage import DateInterval

__all__ = ["Coverage", "DateInterval"]


class Coverage:
    """Coverage data for screener queries."""

    def __init__(self) -> None:
        self._data: dict[str, list[DateInterval]] = {}

    def add(self, symbol: str, interval: DateInterval) -> None:
        self._data.setdefault(symbol, []).append(interval)

    def intervals(self, symbol: str) -> list[DateInterval]:
        return self._data.get(symbol, [])
