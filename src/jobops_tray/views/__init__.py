from __future__ import annotations

"""Views package consolidating GUI code.

The heavy Qt GUI implementation was moved to :pymod:`jobops.views.app`.
Importing this package (``jobops.views``) will **not** import the Qt
bindings immediately—only when :pyfunc:`jobops.views.app.main` or
:pyclass:`jobops.views.app.JobOpsQtApplication` is actually needed.  This
keeps non-GUI usage of the package lightweight.
"""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

__all__ = [
    "app",
    "JobOpsQtApplication",
]

_app_module: ModuleType | None = None


def _lazy_app() -> ModuleType:
    global _app_module
    if _app_module is None:
        _app_module = import_module("jobops.views.app")
    return _app_module


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name == "app":
        return _lazy_app()
    if name == "JobOpsQtApplication":
        return getattr(_lazy_app(), name)
    raise AttributeError(name)


if TYPE_CHECKING:
    from jobops.views.app import JobOpsQtApplication  # noqa: F401
