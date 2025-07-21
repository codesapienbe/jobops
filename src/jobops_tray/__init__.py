"""JobOps package root stub.

Provides lightweight imports and delegates GUI functionality to
`jobops.views.app` to keep top-level package clean.
"""
from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, TYPE_CHECKING

__all__ = [
    "main",
    "JobOpsQtApplication",
]

_gui_module: ModuleType | None = None


def _gui() -> ModuleType:  # Lazy loader for heavy Qt code
    global _gui_module
    if _gui_module is None:
        _gui_module = import_module("jobops.views.app")
    return _gui_module


def main(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """Console-script entry-point, delegates to `jobops.views.app.main`."""
    _gui().main(*args, **kwargs)


if TYPE_CHECKING:
    from jobops.views.app import JobOpsQtApplication  # noqa: F401


class _LazyAttr:
    def __init__(self, name: str) -> None:
        self._name = name

    def __get__(self, _obj: Any, _owner: type | None = None) -> Any:
        return getattr(_gui(), self._name)


JobOpsQtApplication = _LazyAttr("JobOpsQtApplication")  # type: ignore 