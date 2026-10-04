# V-CAPAT PRO v1.1.2 Build Hotfix

This hotfix fixes the Windows release script rejecting a valid Python 3.12 environment.

- Reuses an existing `.venv` when it is Python 3.11 or 3.12 x64.
- Prefers Python 3.12 when creating a new environment, then falls back to Python 3.11.
- Keeps the same test, validation, PyInstaller build, executable smoke-test, packaging, and SHA-256 release gates.
- Updates `run_windows.bat` to support Python 3.12 as well as 3.11.

If an old unsupported `.venv` exists, delete it and rerun `build_release.bat`.
