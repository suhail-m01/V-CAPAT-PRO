# V-CAPAT PRO · Technical report (prototype edition)

## Abstract

This prototype investigates the **coarse acquisition and tracking** stage of a free-space optical communications link. A virtual focal-plane camera observes a moving optical beacon within a seeded world. A classical computer-vision detector locates the spot, a constant-velocity Kalman estimator smooths and predicts its position, and dual PID loops drive camera pan and tilt. The same detection/tracking pipeline can process an external video or webcam stream; a video with labelled truth supports objective centroid-error evaluation. The software exports per-frame evidence and explicit pass/fail/N/A assessments. This document describes the *implemented* system, not the entire 55-item research vision.

## Architecture and trust boundaries

```
Scenario JSON -> seeded world/trajectory -> ROI camera -> disturbances -> image
                                                       image -> detector -> Kalman -> PID -> camera
                                                                      |          |
video/webcam ---------------------------------------------------------+          +-> metrics / GUI / reports
CSV ground truth -----------------------------------------------> metrics ONLY
```

Truth is never passed to the detector or the controller. A `Scenario` is validated at load time and serialized with every exported run. The Python engine is shared by Qt, HTTP and headless entry points. The web server uses `ThreadingHTTPServer`, a simulation worker and a re-entrant lock for consistent snapshots. It is an unprotected local demonstration interface, not an internet-ready service.

## Virtual scene and deterministic time

The default world is a seeded 2000×2000 monochrome raster with 240 stars at density 0.00006. A 640×480 affine ROI extracts the camera frame, so the full world is not re-rendered on every update. Each target follows a world-coordinate trajectory; straight, circular, figure-eight, random walk, spiral, sinusoidal and five role-inspired kinematic presets are available. The last five are *not* orbital propagation. Target shape can be square, disk, Gaussian or an approximate Airy-like profile. Atmospheric modes adjust contrast and blur or add line streaks/wave-like warping. Gaussian, Poisson and salt/pepper image noise, camera jitter and platform motion can be composed. The seeded random generator is local to each simulator. Simulated elapsed time advances by `1/update_hz` per frame, even in faster-than-real-time headless execution.

## Image detection

The default detector smooths a grayscale image, thresholds relative to median/intensity variation, performs morphological opening and extracts connected components. Plausible components are filtered by area, extent and peak contrast. For a candidate bounding region with local baseline `b` and pixel intensities `I`, the subpixel centroid is calculated with weights `w=(max(I-b,0))^1.4`:

`x̂ = Σ(x w) / Σw`, `ŷ = Σ(y w) / Σw`.

The ranking combines area, local brightness, aspect ratio and compactness; a prediction-distance penalty biases the selection toward the current track. A gating radius rejects candidates far from an established track. For an initially ambiguous multi-beacon scene, viewport centre is an explicit acquisition prior (not simulator truth). The alternative top-hat detector removes low-frequency background with a morphological operation; template mode correlates a Gaussian-shaped kernel; Lucas–Kanade optical flow propagates a previous point and falls back to CV detection when flow confidence collapses. These methods are compared on independently reset, identically seeded full-loop runs.

## Tracking and state transitions

The Kalman state is `[x,y,vx,vy]ᵀ` in camera pixels and pixels/second. Its transition is

```
F(dt) = [[1,0,dt,0], [0,1,0,dt], [0,0,1,0], [0,0,0,1]]
x⁻ = F x;  P⁻ = F P Fᵀ + Q
K = P⁻ Hᵀ(H P⁻ Hᵀ + R)⁻¹
x = x⁻ + K(z - Hx⁻);  P = (I-KH)P⁻
```

Here `H` selects position, `R=5I` is a simple pixel-domain measurement covariance, and `Q` models process acceleration plus a small diagonal floor. These are prototype tunings, not sensor-characterized covariances. Three successive detections establish a lock. Five misses move a lock into COASTING; 20 misses trigger REACQUIRING. The estimator continues predicting during short gaps. After the longer REACQUIRING transition, the detector discards the stale position gate and searches the entire current image for plausible spots; the Kalman state is re-seeded from the resulting image candidate, not simulator truth. Camera steering still uses a bounded selectable spiral/raster/random search pattern rather than a validated spaceborne search design.

## Pan/tilt control and units

A camera-frame position offset becomes angle via `θx=(x-W/2)FOVx/W` and `θy=(y-H/2)FOVy/H`. Each channel commands angular speed using

`u=clip(Kp θ + Ki ∫θdt + Kd dθ/dt, -u_max, +u_max)`.

The prototype defaults are `Kp=14`, `Ki=0.3`, `Kd=0.12`; the integral is bounded and only accepted when the unsaturated control is below its limit or would reduce saturation. A small deadband reduces micro-jitter. The virtual camera integrates angular speed and converts accumulated angle back to world-pixel displacement. Because the target moves in world coordinates, a controller can be evaluated without access to truth.

## Metrology and compliance

For visible, labelled frame `i`, detector error is `ec(i)=sqrt((xd-xgt)²+(yd-ygt)²)`. Simulator pointing error is `ep(i)=sqrt((xgt-W/2)²+(ygt-H/2)²)`. RMSE is `sqrt(mean(e²))` over frames with available values. Acquisition is the first `LOCKED` frame with a correct designated-beacon match; target-loss fraction is one minus **correctly** locked visible frames divided by all visible frames. Reacquisition is measured only for completed loss/recovery events. Processing speed is `1000/mean(processing_ms)` and does not assert that the source itself delivers that many frames per second. For simulator mode, the tracking-error gate compares pointing RMSE to 10 px. For prerecorded video, pan/tilt is bypassed, so the gate compares detector centroid RMSE to 10 px instead. Missing truth or a missing completed recovery produces **N/A**, not PASS. Very short runs can fail the strict `<5%` loss rule simply because three lock-establishment frames consume a substantial fraction of the run; this is a faithful consequence of the stated denominator.

The optical-link bar is `100 × exp(-(ep/105)²) × atmospheric_attenuation`, with a displayed throughput proxy of five gigabits/second at 100%. Without simulator truth it uses detection confidence as a display proxy. This is *not* a physically calibrated link budget or BER model and must not be interpreted as a measured communications rate.

## Verification and reproducibility

Automated regression tests cover all trajectory outputs, synthetic beacon detection by each method, Kalman noise suppression, PID saturation, compliance failures/N/A, scenario replay, video-without-truth behavior and export. The bundled MP4 plus matching truth CSV permit a repeatable non-simulator benchmark. A two-image signal-injection test shifts a beacon by precisely five pixels and checks recovered centroid displacement within half a pixel. A detector comparison uses one scenario seed per method. A 20-case stress matrix crosses five atmospheric presets with four trajectory classes, varying noise and size. These are short, isolated tests—not a certified environmental qualification campaign.

Example 300-frame clear-circle run in this workspace (software timings vary by host): acquisition approximately 0.1 s; centroid RMSE ~0.1 px; pointing RMSE ~7–8 px; target loss ~0.7%; average processing several hundred FPS. The corresponding report is generated locally with `python main.py --headless --frames 300`. Results are not universal performance guarantees, and reacquisition is N/A when no loss was exercised. Under long fog/occlusion, tracking can fail; reports record the failure.

## Deployment and remaining engineering work

The `build.bat` recipe packages a Windows application using PyInstaller; Windows output must be built and qualified **on Windows**. Validation still needed for codec compatibility, monitor DPI, cold-start time and clean-machine dependencies. Research features not yet delivered include calibrated wave-optics turbulence, physically verified photon/read-noise sensor response, orbit-driven camera motion from user-supplied TLE, learning-based control, constellation-wide handover, authenticated remote service and BER calibration. See `Implementation_Status.md` for a complete boundary. The correct next step is to freeze an evaluation dataset with explicit visibility/ID labels, measure robustness across repeated seeds and profile the worst-case pipeline latency rather than optimize solely for a visually attractive demo.

## Development increment · point-ahead, phase screens and evidence

Point-ahead is enabled in the browser configuration or desktop Link tab. The algorithm estimates world-frame target angular velocity by differencing consecutive detected centroids after adding the known camera-encoder pose; a low-pass filter and a configuration-based rate cap limit image noise. For assumed range `D` and light speed `c`, the optional two-way light-time `τ=2D/c` yields `θlead=ωτ`. In pixel coordinates the overlay and PID command use `Δx=vx_world,estimated τ`, where `vx_world,estimated` comes from consecutive `(x_detected + camera_x)` samples. The familiar `2v sinφ/c` is a velocity/geometry approximation; this prototype uses explicit angular rate and range instead. At terrestrial ranges the lead can be subpixel; 40,000 km is useful for visible demonstrations. Lead remains an optional control aid, not a claim of orbit-accurate point-ahead.

The turbulence mode now filters seeded white noise in Fourier space with a finite-outer-scale `(|k|²+k0²)^(-11/12)` amplitude and short-wavelength damping. This corresponds to a `-11/3` power-spectrum slope away from the regularization. Screen evolution shifts the previous field (frozen-flow surrogate) and mixes a small independent innovation. The field is normalized, and `r0` scales the final **image warp**. True wave-optics propagation would require wavelengths, aperture, altitude-dependent Cn², complex field propagation and independent validation. Those are not provided here.

Manual designation takes an image-space click, matches it to a CV candidate, and seeds the Kalman filter from that candidate. An optional multi-target handover triggers on a large image innovation when an alternate detected spot replaces the current one. Only after this image-space decision is simulator truth used to assign the numeric target ID for audit, never to steer the camera. Correct-beacon lock retention now rejects false locks. Without coded beacon signatures, close/overlapping spots can still be mistaken for each other.

Each export now includes `frames.sqlite` with indexed pointing/centroid errors, `certificate.pdf` (one-page software-generated evidence), and optional browser ZIP download. `GET /api/query?min_error=10&metric=pointing` returns up to 100 indexed outliers from the last export. `N/A` evidence blocks an all-pass badge. Neither this document nor the PDF represents an official ISRO certificate.

## v0.5 source layout and extension boundaries

The application now follows the requested tree: `config/settings.py` validates dataclasses, `core/engine.py` owns the active runtime and event bus, `simulation/` and `disturbance/` synthesize the camera image, `detection/arena.py` dispatches to individual image algorithms, `tracking/` provides Kalman/association helpers, `control/` supplies pan/tilt PID and lead angle, `metrics/` exports evidence, `io/` handles video/webcam/label contracts, and `gui/`/`api/` present the desktop/browser UIs. [The architecture diagram](Architecture_Diagrams/architecture.svg) illustrates the data/truth boundary; [the full project tree](Project_Tree.md) lists each requested source path.

The WebSocket stream under `api/websocket_stream.py` sends unfragmented server-to-browser JSON text frames after an RFC 6455 handshake; it carries metrics only. Control requests stay in REST. Because the local server is unauthenticated, this is suitable only for a trusted demonstration network. The companion QR points to that server's accessible Host. A bounded MP4 writer in `io/session_recorder.py` produces annotated camera footage when explicitly enabled; it does not create a fully edited three-minute promotional video.

The example detector/controller plugins are dynamically loaded trusted Python from `plugins/`; this is an extensibility boundary, **not** process isolation. They are selectable in both control rooms and recorded in config snapshots. Optional ONNX and SB3 adapters require a separately validated beacon model / controller policy; model weights are not supplied. Scientific caveats remain: no current TLE files, no calibrated atmospheric phase-to-intensity propagation, no independently measured FSOC BER, and no official certification claim.

## v0.5 blueprint-connected models and their validity limits

The browser/desktop configuration adds tunable PID proportional/integral/derivative gains and deadband, tracking process/measurement noise and lock thresholds, and three guided search patterns. Optional manual assist convex-combines operator and PID commands only when a usable detection exists. Camera angular speed is bounded; optional acceleration limits the per-step speed change, and digital zoom changes ROI sampling/FOV angular conversion. Optional simplified FPA processing applies exposure-scaled photon Poisson sampling, dark/read noise, and hot pixels before reducing higher-bit-depth simulated samples to the 8-bit CV path. A temperature-dependent camera-frame translation has an optional reference recalibration; this does **not** establish calibration against a real sensor.

The optional `ground_station_look_angles()` accepts user TLE and UTC/latitude/longitude/height, propagates with SGP4, rotates via approximate GMST and projects against a WGS84 ground position. It omits EOP/polar motion, refraction and error budgets; no stale TLE is shipped as live orbital data. Network coverage is an explicitly labelled truth-audit 2D world-plane geometry calculation, separate from control. Spoof mode injects an unlabeled distractor into the simulated image; trust is a hand-designed spatial/brightness consistency score, not cryptographic authentication. Failure warning is a threshold heuristic, not a trained predictor. Link BER/volume use a nominal BPSK AWGN model and quality proxy, not measured laser receiver BER or data transfer.

The fixed-camera baseline compares two same-seed simulator runs; scenario stress/sensitivity and adversarial search are bounded and store their input configuration. Optional scripted demo-video creation generates title cards plus live annotated simulated frames; no audio, official branding, film editing or guaranteed pass claims. [The 55-item audit](Feature_55_Audit.md) identifies which blueprint capabilities require external trained weights, instrument data, source ephemeris, OS build or reviewed qualification.

## Tracking recovery regression (v0.5.1)

A fixed 100 px prediction gate could prevent recovery after a three-second occlusion even when the beacon was visibly in-frame. On entering REACQUIRING, image detection now removes the obsolete prediction prior and seeds Kalman from a visible CV spot, while correct-designated identity remains an evaluation-only audit. The default Kp increase (10→14) reduced lag in the clear/fog and emergency test cases without asserting universal performance. Video EOF no longer increments the frame number without a read. Completed simulator/video sessions now replay explicitly rather than appear frozen after the configured duration. The 13-scenario and external-video measurements, including remaining failures, are preserved in [Tracking Validation](Tracking_Validation.md).
