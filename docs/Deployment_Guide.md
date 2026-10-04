# V-CAPAT PRO Deployment and Standalone Executable Guide

## Release objective
The mandatory SIH software deliverable is a Windows desktop executable that can run without a local Python source checkout. Version 1.1 adds a reproducible release pipeline, packaged-resource self-test, post-build executable verification, version metadata, SHA-256 checksums and an optional GitHub Actions Windows builder.

## Recommended deliverable: verified onedir package
The primary SIH submission format is the verified **onedir** package because Qt/OpenCV applications are more transparent and typically launch faster than a compressed onefile executable.

On Windows 10/11 x64 with Python 3.11 or 3.12 installed, double-click:

```text
build.bat
```

or run:

```powershell
.\build_release.ps1 -Mode onedir
```

The release script performs the following release gate before it creates the ZIP:

1. Creates/reuses `.venv` using Python 3.11 or 3.12 x64.
2. Installs all runtime dependencies and PyInstaller.
3. Verifies imports for OpenCV, NumPy, PySide6, Matplotlib, qrcode and SGP4.
4. Runs the full automated test suite.
5. Runs `validate_mvp.py`.
6. Builds `VCAPAT_PRO.exe` with bundled assets, scenarios, web UI, documentation and plugins.
7. Launches the **built executable itself** with `--self-test`.
8. Confirms the packaged program can load bundled resources, process at least 30 frames and export CSV/JSON/PDF evidence.
9. Packages the application and submission documents.
10. Generates `SHA256SUMS.txt`.

Successful output:

```text
release\VCAPAT_PRO_v1.1.0_Windows_x64.zip
release\SHA256SUMS.txt
```

Inside the ZIP, `VCAPAT_PRO.exe` is the application entry point and `submission_docs` contains the technical report and supporting documents.

## Optional single-file executable
For a single `.exe` plus submission documents:

```text
build_onefile.bat
```

or:

```powershell
.\build_release.ps1 -Mode onefile
```

Output:

```text
release\VCAPAT_PRO_v1.1.0_OneFile.zip
```

A onefile build can start more slowly because its contents are unpacked at runtime. For a live SIH demonstration, keep the verified onedir package as the primary fallback even if you submit the onefile build.

## Build both formats

```text
build_release.bat
```

This builds and smoke-tests both formats.

## No local Windows build setup: GitHub Actions
The repository includes `.github/workflows/windows-release.yml`. Push the project to GitHub, open **Actions -> Build Windows Standalone -> Run workflow**, and download the `VCAPAT-PRO-Windows-x64` artifact after the job passes. The workflow builds on `windows-latest`, runs the same test/validation/release gate and uploads the verified ZIP packages.

## Executable self-test
The standalone build includes a packaged runtime check:

```powershell
VCAPAT_PRO.exe --self-test
```

The command verifies that bundled scenarios, assets, sample benchmark data and the technical report are present; runs the engine; and writes evidence. A zero exit code means the packaged smoke test passed. It does **not** claim flight qualification or guarantee every stress scenario passes all performance targets.

## Manual source run

```powershell
py -3.12 -m venv .venv  # Python 3.11 is also supported
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Browser control room

```powershell
python main.py --web
```

Open `http://127.0.0.1:8000`. Bind to `0.0.0.0` only on a trusted network and use host firewall controls; the MVP server is not designed as an internet-facing security boundary.

## Judge-style benchmark check

```powershell
python main.py --video assets\sample_beacon.mp4 --ground-truth assets\sample_beacon.csv --headless --frames 120
```

## Final submission acceptance checklist
Before copying the release to the SIH submission system or demo laptop, confirm all of the following on the **same Windows machine used for the demo**:

- `build_release.bat` finishes without error.
- The packaged executable self-test passes.
- Desktop GUI opens by double-clicking `VCAPAT_PRO.exe`.
- The PS compliant preset loads.
- Live tracking runs for at least two minutes without a crash.
- The supplied sample MP4 benchmark opens and processes.
- A PDF performance report is generated.
- `VCAPAT_PRO_Technical_Report_v1.1.pdf` opens correctly.
- The release ZIP SHA-256 matches `SHA256SUMS.txt`.
- A backup copy of the onedir release is kept on a USB drive or separate local folder.
