"""Runtime paths that work from source and from PyInstaller bundles."""
from __future__ import annotations
import sys
from pathlib import Path


def bundle_root() -> Path:
    """Return the read-only application resource root.

    PyInstaller exposes bundled data through ``sys._MEIPASS``.  Source runs use
    the repository root.  Keeping this logic in one place avoids resource-path
    regressions between source, onedir and onefile builds.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def writable_default_root() -> Path:
    """Per-user writable root used by packaged builds."""
    return Path.home() / "Documents" / "VCAPAT_PRO"


def resource(*parts: str) -> Path:
    return bundle_root().joinpath(*parts)
