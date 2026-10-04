# V-CAPAT PRO · Honest 55-feature traceability

**RUNNABLE** = bounded working software function; **PARTIAL** = substantial implementation with stated gaps; **INTEGRATION** = needs external asset/hardware/qualification. Entries are not ISRO certification, physical calibration, or promises of performance. User blueprint includes both mandatory and bonus items.

| # | Blueprint feature | Status | Implemented scope and critical limitation | Source |
|---:|---|---|---|---|
| 1 | Virtual World Engine | PARTIAL | Seeded 2000–4000 px scene, 3 backgrounds, clutter, world/FOV minimap. Solid background intensity is grayscale, not an arbitrary RGB picker. | `simulation/world.py` |
| 2 | Target Generator | PARTIAL | Eleven seeded paths, 1–5 beacons, profile/brightness/blink, RGB tint, manual/center/random start, bounce/wrap. Direction/radius and distinct per-beacon spectral ID are not exposed. | `simulation/trajectories.py` |
| 3 | Virtual Pan-Tilt Camera | PARTIAL | Resolution/FOV/rate, angular mapping, optional acceleration and digital zoom, manual arrow steering. No verified joystick/hardware PTZ. | `simulation/camera.py` |
| 4 | Disturbance & Environment | PARTIAL | Six environments, composite noise, jitter, five platform patterns and occlusion. Fourier warp is not calibrated wave optics. | `disturbance/atmosphere.py` |
| 5 | Detection Pipeline | PARTIAL | Four classical detectors, candidate contributions, gated selection and subpixel centroid. No trained YOLO model or temporal persistence score. | `detection/arena.py` |
| 6 | Predictive Tracker | RUNNABLE | Configurable CV Kalman and five states; measured acquisition/reacquisition events in run telemetry. | `core/state_machine.py` |
| 7 | Closed-Loop PID | RUNNABLE | Dual-axis tunable PID, anti-windup, deadband, limits, manual assist and camera speed constraints. | `control/pid.py` |
| 8 | Search & Re-acquisition | PARTIAL | Selectable spiral/raster/seeded random scan and Kalman prediction; ≤1 s recovery is a measured test, not guaranteed. | `control/search.py` |
| 9 | External Video Benchmark | PARTIAL | MP4/AVI/MOV, labelled CSV, bypassed PTZ, pause/seek/step and original/annotated comparison. CSV export is on demand. | `api/rest_server.py` |
| 10 | Dashboard & Visualization | PARTIAL | Desktop/browser feed, map, telemetry and live error/FPS/pan/tilt plots. Canvas/Qt painter replace pyqtgraph; no particle/audio effects. | `api/companion_web/static/app.js` |
| 11 | Metrics & Auto-Reports | RUNNABLE | CSV/JSON/text/PDF/SQLite/PNG export and five PASS/FAIL/N/A checks; certificates are software evidence only. | `metrics/reporter.py` |
| 12 | Scenario Manager | RUNNABLE | Load/save/import/export validated JSON, seeded random case, replay, 13+ presets and persisted startup default. | `io/scenario_manager.py` |
| 13 | Configuration System | PARTIAL | Validated per-module config, Qt tabs, browser controls, import/export, persisted default. Not every detector threshold/report option is exposed. | `config/settings.py` |
| 14 | Data Export & Logging | PARTIAL | Timestamped evidence folders, optional annotated MP4 and screenshot; application diagnostic log and full auto export need deployment setup. | `metrics/reporter.py` |
| 15 | Standalone Packaging | INTEGRATION | Windows PyInstaller build.bat/icon/splash/assets provided. Actual Windows executable and <5 s launch need Windows build/qualification. | `build.bat` |
| 16 | Multi-Algorithm Arena | PARTIAL | Four independent classical CV comparisons and auto heuristic. A fifth YOLO needs trained beacon weights. | `stress/stress_suite.py` |
| 17 | Communication Link Meter | PARTIAL | Atmosphere/pointing quality, BPSK AWGN BER and volume proxies only. No measured optical BER/throughput. | `link/ber_model.py` |
| 18 | Kolmogorov Turbulence | INTEGRATION | Time-correlated Fourier-spectrum visual warp and r0 exposed; calibrated phase propagation/Cn²/scintillation requires wavelength, aperture and validation data. | `disturbance/turbulence.py` |
| 19 | Satellite/UAV Motion | PARTIAL | LEO/UAV/HAPS/aircraft/star kinematic scene paths. Not Keplerian orbit or measured trajectories. | `simulation/trajectories.py` |
| 20 | Predictive Point-Ahead | PARTIAL | Image-derived velocity × assumed light time with optional overlay/control. Not orbital or physical link validation. | `control/lead_angle.py` |
| 21 | Multi-Beacon Handover | PARTIAL | Image-triggered handover, manual designation, event counts. Priority configuration is recorded but not an authenticated scheduler. | `tracking/handover.py` |
| 22 | Algorithm X-Ray | PARTIAL | Candidate breakdown, mask, Kalman ellipse, on-frame overlay. Rejection-reason popup and 0.1× playback are not provided. | `core/engine.py` |
| 23 | Automated Stress Suite | PARTIAL | 20 seeded cases, pass/fail and CSV/JSON matrix. Software PDF evidence sheet and heatmap included; neither is a certified environmental qualification. | `stress/stress_suite.py` |
| 24 | Beam Profiles | PARTIAL | Gaussian, Airy-like, circle and square spots. Coherent speckle/chromatic dispersion/divergence optics uncalibrated. | `disturbance/beam_optics.py` |
| 25 | FPA Sensor Physics | PARTIAL | Optional QE/dark/read/shot noise, hot pixels, exposure, quantization. No measured quantum-efficiency curves or FPA validation. | `disturbance/sensor_physics.py` |
| 26 | Manual + Blended Assist | PARTIAL | Desktop WASD, browser arrows, tunable manual/PID blending. Gamepad not integrated or device-tested. | `control/manual.py` |
| 27 | Cinematic Replay | PARTIAL | MP4 recording and desktop replay/seek; no event bookmarks or timeline overlays in exported replay. | `gui/replay_widget.py` |
| 28 | Plugin Architecture | RUNNABLE | Trusted detector/controller plugins, dynamic loading, examples and developer guide. Plugins are not sandboxed. | `plugins/loader.py` |
| 29 | REST / Headless | RUNNABLE | CLI, REST, WebSocket, JPEG, Python client and local benchmark controls; bind trusted networks only. | `api/rest_server.py` |
| 30 | Live Webcam | PARTIAL | Host-side webcam frame processing and desktop source. Device-dependent; webcam candidate designation/ground truth unavailable. | `io/webcam_source.py` |
| 31 | RL Camera Controller | INTEGRATION | Stable-Baselines adapter exists; no training data, trained policy or validated PID-vs-RL result supplied. | `control/rl_agent.py` |
| 32 | TLE Digital Twin | PARTIAL | User-supplied TLE + SGP4/Ground WGS84 look-angle tool. Not coupled into scene camera, no current bundled TLE or EOP/refraction correction. | `io/tle_loader.py` |
| 33 | Failure Prediction | PARTIAL | Transparent recent-frame heuristic warning; no trained forecaster or verified 2 s lead time. | `metrics/forecast.py` |
| 34 | Adversarial Scenario Search | PARTIAL | Seeded bounded parameter search finds a reproducible weak case. No evolutionary ML generator. | `stress/adversarial.py` |
| 35 | Multi-Spectral Beacon ID | PARTIAL | Optional RGB view, configured beacon color and blink. No distinct per-beacon coded spectral signature or authenticated discrimination. | `simulation/camera.py` |
| 36 | AR-Style HUD | PARTIAL | On-frame reticle, prediction, vectors and optional range/lead HUD helper; no validated range/velocity audio. | `gui/ar_hud.py` |
| 37 | Digital Signal Injection | RUNNABLE | Known +5 px injection with measured displacement, PASS/FAIL and saved experiment JSON. | `stress/stress_suite.py` |
| 38 | Ground Station Network | PARTIAL | Truth-audit world-plane coverage and handover proxy; not orbit-coordinated station telemetry/relay. | `link/network.py` |
| 39 | What-If Sensitivity | PARTIAL | Bounded one-factor seeded sweep and export; not instant live recomputation of every parameter. | `stress/sensitivity.py` |
| 40 | Long-Session Database | PARTIAL | Indexed SQLite export, fast anomaly query and batch inserts. Active telemetry retained in RAM; 1M+ frame streaming unverified. | `metrics/time_series_db.py` |
| 41 | Explainable Scoring | RUNNABLE | Hand-designed area/brightness/shape/prediction penalty breakdown. Not SHAP or a trained AI attribution. | `detection/xai.py` |
| 42 | Spoof Robustness | PARTIAL | Opt-in unlabeled bright distractor + candidate-consistency score. Does not authenticate source or prevent spoofing. | `security/spoof_detector.py` |
| 43 | Thermal Drift | PARTIAL | Temperature-driven pixel offset and reference calibration with reproducible configuration. Not sensor-calibrated. | `disturbance/thermal_drift.py` |
| 44 | LLM Report | INTEGRATION | Deterministic key-free rule-based summary is included; generative LLM requires external provider, key and review. | `metrics/llm_summary.py` |
| 45 | Teaching Mode | PARTIAL | Ten short lessons and self-check in Qt; not a full course with validated certificates. | `gui/tutorial.py` |
| 46 | Judge Demo | PARTIAL | Time-boxed guided script and scenario montage; not a fault-tolerant fully narrated 5-minute automated showcase. | `gui/judge_demo.py` |
| 47 | Splash & Branding | PARTIAL | Logo, icon, splash and consistent theme. No animated splash/light theme/team-provided credits. | `assets/splash.png` |
| 48 | Live Compliance | RUNNABLE | Five live PASS/FAIL/N/A checks; badge is explicitly software evidence, not certification. | `metrics/compliance.py` |
| 49 | Auto Demo Video | PARTIAL | Configurable scripted MP4 montage with scenario title cards; no music/narration/YouTube polish. | `io/demo_video.py` |
| 50 | Wow Scenarios | RUNNABLE | Extra Category 5, Needle, Blackout and five-beacon presets plus existing formation and handover. Outcomes remain honestly measured. | `scenarios/` |
| 51 | Real-Time Visuals | PARTIAL | Responsive styled six-page control room and overlays. Particle/lens flare/audio not included. | `api/companion_web/static/app.css` |
| 52 | Companion Web | RUNNABLE | Local responsive six-page control room, QR and WS/polling. Unauthenticated; trusted network only. | `api/rest_server.py` |
| 53 | Leaderboard vs Baseline | PARTIAL | On-demand identical-seed fixed-camera comparison and local rankings; not a simultaneous live learned-baseline race. | `metrics/baseline.py` |
| 54 | Contextual Help | PARTIAL | Settings tooltips, manual, algorithm explanations and tutorial; searchable universal tooltip/diagram library not included. | `docs/User_Manual.md` |
| 55 | Achievement System | RUNNABLE | Evidence-only badges, desktop view and browser analysis. No fabricated unlocked badges. | `metrics/achievements.py` |

## Submission boundary

Real beacon-trained YOLO and RL weights, calibrated atmospheric phase propagation and BER measurements, live authenticated orbital data, and a verified Windows executable are **not bundled**. Training, lab metrology, and Windows qualification cannot be replaced by a demo toggle. The software report is not an ISRO-issued certificate.
