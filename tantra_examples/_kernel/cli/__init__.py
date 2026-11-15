# mirror: kernel-verbatim port (gap 0004: wheel display/client surface) —
# Decimal-canonical wheel retarget (ex 0006): ParquetBarStore is ``tantra.store``.

from __future__ import annotations

from tantra.store import ParquetBarStore

__all__ = ["_STORE", "get_store"]

_STORE = ParquetBarStore()


def get_store() -> ParquetBarStore:
    """Get the global data store instance."""
    return _STORE
