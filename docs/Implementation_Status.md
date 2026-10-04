# Implementation boundary · V-CAPAT PRO v0.5.0

This repository **follows the specified package tree**. A module existing does not mean a research feature has been validated; capability and limitations are recorded here.

## End-to-end, runnable paths

- **Input:** Seeded simulator, externally supplied MP4/AVI/MOV with optional matching ground truth, local webcam on the machine running Python.
- **Tracking:** Threshold, top-hat, correlation and optical-flow CV; intensity-weighted subpixel centroid; candidate confidence/gating; constant-velocity Kalman; SEARCHING → ACQUIRING → LOCKED → COASTING → REACQUIRING; default dual PID with anti-windup and speed limits.
- **Simulation:** Independent 2000×2000 default world raster, seeded stars, four spot profiles, 11 illustrative trajectories, camera ROI, platform motion, jitter, composable Gaussian/Poisson/salt-pepper image noise, atmospheric presets, time-correlated Fourier-spectrum turbulence **image warp**, and timed beacon occlusion.
- **Interaction:** six-view PySide6 desktop (splash, settings, viewport, X-Ray, minimap, tools menu, controller/detector plugin selection, optional annotated MP4 recording) and six-route local browser mission control (REST, WebSocket metric push with polling fallback, mobile-responsive navigation, QR code, report ZIP download, error query). Ground truth never steers detection or PID.
- **Evidence:** Per-frame CSV, indexed SQLite, JSON, PNG charts, software evidence PDF, text recommendation, optional MP4, reproducible config snapshot and event log. Clear N/A handling when video truth or a completed loss/recovery event is missing.
- **Experiments:** Seeded four-detector comparison, 20-case stress matrix, 5 px signal-injection validation; on-demand desktop sensitivity sweep and bounded parameter adversarial search helper.
- **Extensions:** Two bundled **trusted** detector/controller plugins load into the shared live engine; a rule-based summary works without an LLM key. An optional illustrative sensor exposure model and calibratable thermal offset are connected to simulator frames; SGP4-based look angles accept a user-supplied TLE. Supplied-model RL/ONNX adapters are present but no weights are bundled.

## Interface refinement (v0.4)

The browser uses separate full-page routes for Overview, Live tracking, Scenarios, Video benchmark, Analysis & reports, and Algorithm lab. The desktop has a matching six-page navigation rail, with the pre-existing live controls intact. Navigation does not reset a session; changing a preset or applying configuration intentionally restarts the seeded run. The new pages are views into the existing engine and do not expand any scientific-validation claims. Browser/Qt smoke checks and 31 automated tests cover the expanded interface and backend contracts.

See the [tracking validation matrix](Tracking_Validation.md) for all 13 presets, labelled/unlabelled MP4 checks, fixed recovery issues and remaining stress failures.

## Full-blueprint feature audit (55 items)

[Read the line-by-line audit](Feature_55_Audit.md) or open **Algorithm lab → 55-feature traceability** in the browser (**Help → 55-feature audit** in desktop Qt). Current scope: **12 RUNNABLE bounded software features, 39 PARTIAL features, 4 INTEGRATION-dependent features**. The blueprint's claim that a 55-feature system can be implemented and validated in a day is not evidence. This update connects tunable PID and Kalman settings, search patterns, simple FPA/thermal/spoof modes, scenario import/export/persistence, seeded extra presets, baseline and sensitivity experiments, user-supplied TLE look angles, a Python client, and a scripted silent MP4 montage. None of these changes substitutes for real trained YOLO/RL weights, wave-optics calibration or Windows testing.

## Partial or research-grade-only models

- **Multi-target:** Manual candidate designation and opt-in image-innovation handover work for distinguishable targets. There is no validated beacon-ID signalling, priority scheduler or orbital constellation handover. Identical overlapping spots remain ambiguous. Truth is used only *after* image selection for score/audit identity.
- **Turbulence:** Seeded correlated regularized Kolmogorov/von Kármán-*shaped* Fourier fields are mapped to a bounded image warp. This is not calibrated Cn² wave-optics propagation, scintillation or an ITU-certified phase-screen simulator.
- **Motion:** LEO/UAV/HAPS/aircraft roles are kinematic scene paths, not genuine orbit prediction. TLE support parses user inputs and uses the installed `sgp4` package for approximate ground-station look angles; no current ISS/IRNSS TLE is bundled or represented as live data.
- **Point-ahead/link:** Lead uses image-derived world angular velocity and an assumed 10–40,000 km travel time. Link bar and BER helper are illustrative, **not** a calibrated telecommunications link budget.
- **Optional models:** `assets/models/yolov8n_beacon.onnx` and a trained stable-baselines RL policy are **not shipped**; neither a generic YOLO model nor arbitrary RL weights would constitute a trained beacon tracker. ONNX and RL adapters fail clearly when no compatible weights/dependencies are supplied. These are *not* available in the default GUI algorithm choices.
- **Certification:** `certificate.pdf` is software-produced run evidence, **not** a certificate from ISRO. Stress-suite PDF certification, a complete 10–15 page reviewed technical report and Windows clean-room qualification still require external validation.

## Remaining roadmap

Calibration of the newly integrated illustrative FPA model against measured quantum efficiency/dark current/hot pixels; authenticated multi-spectral IDs; physically validated Kolmogorov wavefront propagation, scintillation and BER; real TLE ground-station azimuth/elevation plots; trained RL/anomaly detector; anti-spoof threat model; station network coordination; million-frame *streaming* storage; LLM report integration; automated narrated demo video. A `*.py` source file under the requested layout may expose a useful bounded adapter/helper rather than the entire 55-feature research ambition.

## Deployment caveats

- The local API/WebSocket is **unauthenticated**; bind only on trusted networks. User-provided plugins execute Python and must be reviewed.
- The report's FPS measures **pipeline processing throughput**, not webcam/video frame capture or desktop rendering cadence. External footage without GT has N/A accuracy, not zero error.
- Seeded replay is reproducible on a consistent NumPy/OpenCV build. Cross-platform bit-identical video encoding is not guaranteed.
- `build.bat` defines a Windows PyInstaller build, but no Windows executable has been produced or tested in this Linux workspace.
