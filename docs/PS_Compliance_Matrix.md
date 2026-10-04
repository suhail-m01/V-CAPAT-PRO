# SIH26169 Problem-Statement Compliance Matrix

This matrix maps the shipped MVP to the supplied FSOC virtual-camera coarse-alignment specification. It describes software implementation, not flight qualification or ISRO certification.

| PS item | MVP implementation | Status |
|---|---|---|
| Virtual scene at least 2000×2000 | `WorldConfig` validation enforces 2000–4000 px in both dimensions | Implemented |
| Monochrome FPA, colour optional | Grayscale is default; colour rendering is optional | Implemented as software sensor model |
| Camera resolution | User-defined 320–1920 × 240–1080; reference mission uses 640×480 | Implemented |
| Camera FOV | User-defined; reference mission uses 4°×3° | Implemented |
| Camera rate ≥30 Hz | Validator and GUI enforce 30–60 Hz | Implemented |
| Initial camera at scene centre | Zero pan/tilt maps to world centre | Implemented |
| Beacon target | Gaussian/square/circle/Airy-like spot renderers | Implemented |
| At least one target; multiple optional | 1–5 targets with designation/handover | Implemented |
| Target size 5–20 × 5–20 px | Independent width/height fields, each 5–20 px | Implemented |
| Initial target location | Manual, centre, seeded random | Implemented |
| Straight/circular/figure-8/random motion | All four plus spiral, sinusoidal and illustrative mission profiles | Implemented |
| Pan/tilt speed 5–10°/s | Validator/GUI enforce 5–10°/s; default 5°/s | Implemented |
| Control update ≥20 Hz | Camera loop is ≥30 Hz in PS-compliant mode | Implemented |
| Salt & pepper / Gaussian / Poisson | Selectable singly or combined | Implemented |
| Noise SD ≤20 px | Enforced | Implemented |
| Camera jitter ±20 px/frame max | Enforced | Implemented |
| Atmosphere: clear/haze/fog/rain/low light | All required modes plus turbulence | Implemented |
| User-defined contrast/brightness reduction | `contrast_scale` and `brightness_offset` controls | Implemented |
| Platform motion ±20 px/frame max | Per-frame platform offset delta is clamped to configurable maximum ≤20 | Implemented |
| Automatic beacon detection | Classical CV and TinyML-assisted candidate ranking | Implemented |
| AI-assisted tracking requirement | `tinyml` / `ai_auto` use a deterministic learned logistic candidate classifier; Kalman/PID remain interpretable | Implemented MVP |
| Continuous tracking | Kalman state estimator + lock state machine | Implemented |
| Virtual pan-tilt repositioning | Dual PID with speed limits and optional acceleration limit | Implemented |
| Acquisition ≤2 s | Measured and reported from first correct lock | Evaluation metric implemented |
| Tracking error ≤10 px | Pointing RMSE (simulator) / centroid RMSE (labelled video) | Evaluation metric implemented |
| Target loss <5% | Visible designated-target loss percentage | Evaluation metric implemented |
| Re-acquisition ≤1 s | Loss-to-correct-lock recovery timing | Evaluation metric implemented |
| Processing ≥20 FPS | Pipeline processing FPS, not source/video FPS | Evaluation metric implemented |
| Judge MP4 bypassing PTZ | External video mode bypasses simulator camera actuation | Implemented |
| Centroiding error / RMSE / lock retention | Recorded per frame and summarized | Implemented |
| Automatic performance logs | CSV, JSON, SQLite, charts, PDF certificate/report | Implemented |
| Standalone application | PySide6 desktop + PyInstaller Windows build scripts | Build-ready; Windows executable must be produced/tested on Windows |
| Source code | Modular package with tests | Implemented |
| Technical report | `docs/SIH_Technical_Report.md` plus architecture/validation docs | Included |
| User manual | `docs/User_Manual.md` | Included |

## Reference mission

`scenarios/ps_compliant_reference.json` is the canonical requirement-demo preset. `python validate_mvp.py` performs static compliance checks and a 120-frame pipeline smoke test.
