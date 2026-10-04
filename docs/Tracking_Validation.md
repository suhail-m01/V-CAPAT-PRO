# V-CAPAT PRO — Tracking validation and repair

This is a **software-only, local run**, not ISRO certification. The simulator cases below each processed **300 frames (10 s simulated at 30 Hz)** on this machine; timings and FPS vary by host. Video processed the **120-frame bundled MP4**. Full machine-readable results: [`reports/tracking_diagnostics.json`](../reports/tracking_diagnostics.json).

## Reproducible problems found and fixed

1. **Stale prediction blocked reacquisition.** During a long gap the Kalman estimate drifted beyond the fixed 100 px detection gate. Visible candidates were scored but permanently rejected. In `REACQUIRING`, the detector now searches the full image without the stale association prior and resets the filter from the reacquired *image measurement*, not simulator truth. The three-second blackout now returns to `LOCKED` in a 360-frame run. A regression test covers this.
2. **Completed run appeared impossible to resume.** After the scenario's configured 60 s, `Resume` executed one frame then immediately stopped. The UI now says **Replay** for a completed simulator/video; pressing it starts a fresh run/segment. Pause/Resume within an unfinished run still preserves state. The browser and desktop were both checked.
3. **Video EOF advanced the frame counter without a frame.** Frame numbering now increments only after a successful video read. Seek and EOF replay are regression-tested.
4. **Nominal control lag.** The default simulator PID Kp was tuned from 10 to 14; the fog/figure-eight case decreased from approximately 11.3 px RMSE to 8.8 px and the emergency case from approximately 10.1 px to 9.3 px at 300 frames on this build. No claim of universally optimal gains.
5. **Misleading status.** The simulator now displays a **FALSE TARGET** audit warning when image-only tracking locks onto a spot that ground-truth evaluation says is not the designated beacon. Truth never steers detector or motor output.

## Simulator matrix (fixed seed, 300 frames each)

`A / P / L / R / F` = acquisition ≤2 s / pointing RMSE ≤10 px / visible-target loss <5% / reacquisition ≤1 s / pipeline processing ≥20 FPS. `—` means **N/A**, not PASS. Three seconds of intentional blackout cannot satisfy a one-second *loss-to-recovery* requirement; it is correctly marked FAIL.

| Scenario | End state | RMSE px | Loss % | Pipeline FPS | A / P / L / R / F |
|---|---|---:|---:|---:|---|
| `category5_everything` | LOCKED | 22.64 | 10.00 | 14.6 | P / F / F / — / F |
| `constellation_five` | LOCKED | 2.95 | 0.67 | 200.4 | P / P / P / — / P |
| `easy_clear_circular` | LOCKED | 5.72 | 0.67 | 307.8 | P / P / P / — / P |
| `emergency_maneuver` | LOCKED | 9.32 | 0.74 | 51.1 | P / P / P / P / P |
| `extreme_multi_target_occlusion` | LOCKED | 19.46 | 0.71 | 70.6 | P / F / P / P / P |
| `formation_flight` | LOCKED | 3.23 | 0.67 | 70.8 | P / P / P / — / P |
| `handover_sequence` | LOCKED | 6.29 | 0.71 | 82.1 | P / P / P / P / P |
| `hard_full_chaos` | COASTING | 3.31 | 0.74 | 67.2 | P / P / P / P / P |
| `iss_overpass` | LOCKED | 36.00 | 7.33 | 74.3 | P / F / F / P / P |
| `loitering_uav` | LOCKED | 1.90 | 0.67 | 77.5 | P / P / P / — / P |
| `medium_foggy_figure8` | LOCKED | 8.84 | 0.67 | 75.4 | P / P / P / — / P |
| `needle_in_haystack` | LOCKED | 7.47 | 0.67 | 235.2 | P / P / P / — / P |
| `total_blackout` | LOCKED | 19.50 | 0.95 | 241.7 | P / F / P / F / P |

**Outcome:** All 13 seeded simulator scenarios execute without a runtime exception. Nine have no measured FAIL among the checks exercised; four intentionally demanding scenarios still fail at least one limit: `category5_everything` (RMSE, loss, FPS), `extreme_multi_target_occlusion` (RMSE), `iss_overpass` (RMSE and loss), and `total_blackout` (RMSE and recovery time). `hard_full_chaos` ends in `COASTING` at 10 s even though its run-average measured checks are not FAIL; that final state must not be misrepresented as continuously locked. Unexercised recovery checks remain N/A.

## External MP4 benchmark

| Input | Frames | End state | Centroid RMSE | Acquisition / centroid / loss / recovery / FPS |
|---|---:|---|---:|---|
| `bundled_video_with_ground_truth` | 120 | LOCKED | 0.121 px | P / P / P / — / P |
| `bundled_video_without_ground_truth` | 120 | LOCKED | N/A px | — / — / — / — / P |

The labelled MP4 uses **centroid** RMSE, because prerecorded footage bypasses pan/tilt. The unlabelled MP4 still runs detection but has **N/A** accuracy, acquisition and loss; it is not credited with passing them.

## Tests and interfaces executed

- `python -m pytest -q` — **27 passed**, after installing every declared dependency with `python -m pip install -r requirements.txt`. A first run in the unconfigured sandbox had 2 dependency errors (`qrcode`, `sgp4`); they disappeared after installation.
- Each of 13 seeded simulator presets — ran 300 frames and calculated five independent compliance results.
- Bundled video with and without matching truth CSV — processed 120 frames in each mode.
- Browser smoke check — all six pages and 55-feature matrix loaded without JavaScript page errors; Replay button, MP4 upload, truth upload and video seek were exercised.
- Preview compatibility follow-up — the tracking/benchmark/analysis charts and world map now use **inline SVG**, not browser canvas or remotely loaded chart images. All three charts and the map rendered in headless Chromium with Canvas deliberately disabled; chart toggles worked with no JavaScript page errors. This addresses the blank/broken tracking-error panel shown in the user screenshot.
- Desktop offscreen smoke check — six views, completed-run Replay, MP4 frame-step and feature audit were exercised.
- API end-to-end regression — page navigation preserves a live engine; scenario saves/imports, experiment ZIP, bounded stress helpers, EOF replay and duration-complete replay are covered in automated tests.

**Not validated here:** a physical webcam device, trained RL/YOLO weights, link BER measured on hardware, true Cn²-calibrated turbulence, a Windows-built `.exe`, or real satellite tracking. The unauthenticated local web API should only be used on a trusted network.

## Try the repaired tracking preview

1. Select **Easy · Clear Orbit** or **Medium · Fog / Figure Eight** in Scenarios and open **Live tracking**. A run is meant to settle into LOCKED; use the scenario data above for expectations.
2. To inspect loss/recovery, select **Total Blackout**. The beacon is deliberately hidden for three seconds. It now reacquires afterwards, but correctly fails the ≤1 s loss-to-recovery rule.
3. If the configured duration expires, press **Replay** (or **Reset**) instead of waiting for the previous session to advance. The evidence of the previous run can be exported from Analysis before replaying.
