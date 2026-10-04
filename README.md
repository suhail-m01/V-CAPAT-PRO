<<<<<<< HEAD
# V-CAPAT PRO · v1.1.4 MVP

**Virtual Camera Acquisition, Pointing And Tracking** — a deployable FSOC coarse-alignment MVP aligned to SIH26169, with requirement-enforced simulation, AI-assisted beacon candidate ranking, tracking/control, benchmark-video evaluation and automatic evidence reports. [Browse the complete project tree](docs/Project_Tree.md) and [view the architecture diagram](docs/Architecture_Diagrams/architecture.svg).

> **Scope:** this is a hackathon/research MVP, not an ISRO-certified flight system. The supplied problem-statement items are mapped in [PS Compliance Matrix](docs/PS_Compliance_Matrix.md); scientific limitations remain explicit.


## Run

Python 3.10–3.13. From the `vcapat-pro/` directory:

```bash
python -m pip install -r requirements.txt
python main.py --web                                      # local browser control room (127.0.0.1:8000)
python main.py --web --host 0.0.0.0 --port 8000           # trusted-LAN/container exposure
python main.py                                          # PySide6 desktop control room
python main.py --headless --frames 300                  # ten seconds at 30 simulated Hz
python main.py --scenario scenarios/handover_sequence.json --headless --frames 390
python main.py --video assets/sample_beacon.mp4 --ground-truth assets/sample_beacon.csv --headless --frames 120
python main.py --demo-video 180                      # scripted, silent 3-minute MP4 montage
python validate_mvp.py                                  # PS checks + tracking smoke test
python -m pytest -q
```

For measured tracking behavior and deliberate stress-case failures, read the [tracking validation report](docs/Tracking_Validation.md).

The browser control room is at `http://localhost:8000/`. Its six real routes are `/` **Overview**, `/mission` **Live tracking**, `/scenarios` **Scenarios**, `/benchmark` **Video benchmark**, `/analysis` **Analysis & reports**, and `/engineering` **Algorithm lab**. Each is a separate server-rendered document with its own purpose and controls; full-page navigation retains the same server-side engine session. A browser WebSocket pushes telemetry; REST polling takes over if the connection is unavailable. The webcam operates on the **machine running Python** (desktop Open webcam or CLI `--webcam 0`), not remotely on a browser user's phone.


## PS-compliant MVP additions

- World validation now enforces at least **2000×2000** pixels; camera rate is **30–60 Hz** and pan/tilt limits are **5–10°/s**.
- Beacon width and height are independently configurable from **5–20 px**; the canonical preset uses a 10×10 square beacon with seeded-random initial location.
- Platform motion now has a true per-frame displacement clamp of **≤20 px/frame**; atmospheric contrast and brightness are user-adjustable.
- `ai_auto` fuses interpretable candidate scoring with a deterministic learned TinyML probability without external model downloads.
- `validate_mvp.py`, `tests/test_ps_compliance.py`, a canonical PS scenario, Docker web deployment, and hardened Windows build scripts are included.

## Included functionality

- Deterministic world/targets/camera, four classical CV methods plus built-in TinyML-assisted candidate ranking (`tinyml`/`ai_auto`), a constant-velocity Kalman estimator, five-state lock machine, pan/tilt PID, gated multi-target designation and optional image-innovation handover.
- Gaussian/Poisson/salt-pepper noise, PS-bounded jitter and platform motion, clear/haze/fog/rain/low-light modes, user-controlled contrast/brightness, an illustrative turbulence warp, optional lead-angle compensation, and a **modelled** (not measured) link-quality bar.
- Simulator, MP4/AVI/MOV benchmark with optional zero-based ground-truth CSV, and local webcam. Replay/scrub a chosen MP4 from desktop Tools.
- Six-view Qt desktop mission control (Overview, Live tracking, Scenarios, Video benchmark, Analysis & reports, Algorithm lab) with tabbed settings, splash, X-Ray, minimap, charts, manual keyboard controls, plugins, tools gallery and optional annotated MP4 recording.
- Six-page browser mission control with responsive navigation, QR to the current host, `/ws` metric stream, CV stress/comparison/self-tests, recording, CSV/JSON/PNG/PDF/SQLite report generation, ZIP download and indexed error query.
- Fourteen seeded scenarios including `PS Compliant Reference Mission` (including four demanding demo cases), matched example MP4/CSV, two trusted example plugins, 31 automated tests and sample evidence under `reports/`.

## Newly connected blueprint controls

- **Config:** tunable PID/deadband, Kalman thresholds/noise and search pattern, manual assist, camera acceleration/zoom/color/start pose, random/center starts, target boundary, optional simplified sensor noise/hot pixels, spoof distractor and calibratable thermal offset. Defaults preserve the original reproducible pipeline.
- **Scenarios:** JSON save/import/export, random seeded tests and a persisted startup default (stored in the output folder); 13 bundled cases. The desktop File menu and browser Scenarios page expose them.
- **Experiments:** noise sensitivity and bounded weak-case search, fixed-camera baseline ranking, an optional raw/annotated benchmark comparison, and simple non-ML degradation warnings. Engineering includes a user-supplied TLE azimuth/elevation calculator and a labelled world-plane multi-station coverage proxy.
- **Evidence:** optional silent demo MP4 (`--demo-video 180`), feature-audit screen, and a Python client in `vcapat/api/client.py`. Local REST is not authenticated; use a trusted network.

## Package boundaries

| Package | Responsibility |
|---|---|
| `vcapat/config`, `core` | validated scenario dataclasses, engine, lock states, event bus |
| `simulation`, `disturbance` | world raster, target, trajectory, camera, atmospheric imaging and sensor helpers |
| `detection`, `tracking`, `control` | CV algorithms/arena, Kalman, PID, search, multi-target association, lead angle |
| `link`, `metrics` | illustrative link proxy, metrics/compliance, indexed SQLite and PDF report |
| `io`, `plugins`, `security`, `stress`, `utils` | video/webcam/ground truth, trusted extension loader, checks and reproducible experiments |
| `gui`, `api` | PySide6 desktop panels, local REST/WebSocket and companion browser dashboard |

### Evaluation definitions

**Simulator pointing error:** labelled target-to-centre distance. **Video centroid error:** detector-to-labelled-target distance in the original frame. The 10 px check uses pointing RMSE in simulator mode and centroid RMSE in video mode. Lock retention only counts correctly locked, *visible designated* targets; missing ground truth produces **N/A**, not zero error or PASS. Acquisition is the first correct `LOCKED` frame. Pipeline FPS is `1000/mean(pipeline_ms)`, not source FPS or GUI refresh. See [Technical Report](docs/Technical_Report.md) for algorithms and [User Manual](docs/User_Manual.md) for controls/API.

## Plugins and optional integrations

`plugins/example_detector_plugin.py` and `plugins/example_controller_plugin.py` implement the interfaces in `vcapat/plugins/interfaces.py`. They can be selected from the detector/controller controls (`plugin:example_detector_plugin` and `plugin:example_controller_plugin`). **Only load plugins you trust; plugins execute Python code.** See [Plugin Developer Guide](docs/Plugin_Developer_Guide.md).

A self-contained NumPy TinyML classifier is included and used by `ai_auto`; it is trained deterministically from synthetic candidate-feature distributions at startup. `assets/models/yolov8n_beacon.onnx` is still **not provided** because a mission-trained neural model cannot be honestly fabricated. `vcapat/detection/yolo_onnx.py` can load a compatible user-supplied ONNX model after its output decoder is adapted. An RL `.zip` policy remains user-supplied. SGP4 is now installed by the requirements and can calculate approximate look angles from a **user-supplied current TLE** in Algorithm Lab; it does not drive the scene camera or supply orbital truth to the detector. Neither trained-model adapter is active in the default pipeline.

## Windows standalone release

Run `build_release.bat` **on Windows** with Python 3.11 or 3.12 x64 to build both verified formats, or use `build.bat` for the recommended onedir package and `build_onefile.bat` for a single-file executable. Version 1.1 runs all tests and `validate_mvp.py`, builds with dedicated PyInstaller spec files, launches the **built executable itself** with `--self-test`, packages the technical report, and writes SHA-256 checksums before declaring a release. The same gate is available through `.github/workflows/windows-release.yml` on a Windows GitHub Actions runner. See [Deployment Guide](docs/Deployment_Guide.md). A Windows `.exe` still has to be produced on Windows/Windows CI; this Linux workspace does not pretend to emit a verified PE binary.

The formal mandatory report is included as [VCAPAT_PRO_Technical_Report_v1.1.pdf](docs/VCAPAT_PRO_Technical_Report_v1.1.pdf) with its editable DOCX source.

## Scientific limitations

The LEO/UAV/HAPS motion presets are illustrative, not orbit propagation; the turbulence pixel warp is not Cn²-calibrated wave optics; the link bar is not BER validation. Identical beacons that cross can confuse association. The PDF is software-generated evidence, **not official ISRO certification**. The local API/QR/WebSocket server has no authentication: bind to trusted networks only.


## Windows performance hotfix (v1.1.4)

The real-time disturbance path was optimized for Windows release builds without lowering the SIH performance requirement. Gaussian noise now uses deterministic OpenCV-native generation, salt/pepper noise touches only requested impulse pixels, and adaptive/top-hat thresholds use OpenCV-native statistics. The `medium_foggy_figure8` regression still requires measured average processing throughput of **>= 20 FPS**; the test threshold was not weakened.

## Windows release build (v1.1.3 hotfix)

Run `build_release.bat`. Release metadata now lives under `packaging/` and is not removed by build cleanup. The release script also retries archive creation when Windows temporarily locks PyInstaller files.
=======
# V-CAPAT-PRO
V-CAPAT PRO Virtual Camera Acquisition, Pointing &amp; Tracking System for Mobile FSOC Terminals  SIH PS: SIH26169  This release contains the Windows executable version of the V-CAPAT.  Recommended: VCAPAT_PRO_v1.1.4_Windows_x64.zip  Also include: Single-file Windows executable package SHA-256 checksums Technical report User documentation.
>>>>>>> 881c8a036a489c5a8876960043f11f79007a4867
