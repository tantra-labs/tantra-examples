"""Interactive data-root seam (plan 0004 T15.2): the user-facing choice.

When a data root is absent, offer download / dummy / Monte-Carlo and invoke
the chosen mode through ``provision()``. Modes not yet wired surface as a
failed ``ProvisionJob`` with a clear milestone pointer (no silent empty data).
"""

from __future__ import annotations

from collections.abc import Callable

from tantra_examples.provision import provision
from tantra_examples.provision.contracts import ProvisionJob, ProvisionRequest
from tantra_examples.provision.dummy import is_complete
from tantra_examples.provision.layout import Dataset, Mode, resolve_data_root


def choose_mode(prompt: str | None = None) -> Mode:
    """Interactively pick a provisioning mode; invalid input re-prompts."""
    while True:
        answer = input(prompt if prompt is not None else "1=download, 2=dummy, 3=monte-carlo: ")
        choice = answer.strip()
        if choice == "1":
            return Mode.DOWNLOAD
        if choice == "2":
            return Mode.DUMMY
        if choice == "3":
            return Mode.MONTE_CARLO
        print(f"Invalid choice {choice!r}; enter 1, 2 or 3.")


def ensure_data_root(
    data_root: str | None = None, *, chooser: Callable[[], Mode] | None = None
) -> ProvisionJob:
    """Resolve the data root, skipping when complete, otherwise provision it."""
    root = resolve_data_root(data_root)
    if is_complete(root):
        return ProvisionJob(
            job_id="",
            dataset=Dataset.NSE_1D_CATALOG,
            mode=Mode.DUMMY,
            status="skipped",
            root=root,
        )
    mode = chooser() if chooser is not None else choose_mode()
    req = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=mode, data_root=str(root))
    try:
        return provision(req)
    except NotImplementedError as exc:
        return ProvisionJob(
            job_id="",
            dataset=req.dataset,
            mode=mode,
            status="failed",
            root=root,
            error=str(exc),
        )


__all__ = ["choose_mode", "ensure_data_root"]
