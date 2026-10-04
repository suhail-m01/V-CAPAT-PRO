# V-CAPAT PRO · User manual

## 1. Install and launch

Install Python 3.10–3.13. In the project directory run `python -m pip install -r requirements.txt`. Start the desktop app with `python main.py`, or the browser control room with `python main.py --web --port 8000` and open `http://localhost:8000`. The browser frontend uses local server APIs and requires no internet. Use `python main.py --headless --frames 300` for a reproducible 10-second simulated run at 30 Hz. On Windows, run `build.bat` to build with PyInstaller, then test the generated executable on a clean machine. In a packaged build, default output goes to `Documents/VCAPAT_PRO/reports`.

## 2. A first mission

1. Start **Easy · Clear Orbit**. Watch the green selected-candidate box and red centroid move toward the cyan centre reticle. The status changes `SEARCHING → ACQUIRING → LOCKED` after three detections.
2. Read the right-hand **telemetry**: FPS is pipeline throughput; pointing error measures target-to-centre distance; centroid error compares the detector with simulator truth.
3. Check the world minimap. The cyan rectangle is the camera FOV; the green dot is the target.
4. Pause and **Export report**. Open the timestamped folder under `reports/` for `frames.csv`, `frames.sqlite`, `summary.json`, `compliance.json`, `certificate.pdf`, charts and a final annotated image. The PDF is a software report, not official certification.
5. Select **Medium · Fog / Figure Eight**, then **Hard · Full Chaos**. Failing tests are visible; no metric is fabricated to force compliance.

## 3. Browser navigation and controls

The browser has six distinct pages. Navigation loads a new document but keeps the same running engine on the Python server. Only loading a preset, applying configuration, opening a new video, resetting, or seeking intentionally changes the run/segment.

| Route | Purpose |
|---|---|
| `/` | Overview of station state, alignment chain and evidence readiness |
| `/mission` | Live camera, beacon designation, X-Ray, pause/reset, recording, error plot and minimap |
| `/scenarios` | Thirteen seeded missions and controlled disturbance, trajectory, detector and controller configuration |
| `/benchmark` | MP4/AVI/MOV upload, optional ground-truth CSV, frame seek/step and centroid metrics |
| `/analysis` | RMSE, five requirement checks, charts, indexed anomaly query, experiment suite and report ZIP |
| `/engineering` | Candidate score components, optical pipeline, lead model, plugin list and companion QR |

On **Live tracking**, click a visible candidate in simulator mode to designate it. Toggle X-Ray to show scored candidates, the binary mask and Kalman uncertainty. Record MP4 before exporting if a clip should be included. On **Scenarios**, selecting a preset restarts with its fixed seed; changing custom controls and clicking Apply also restarts. Opt-in automatic handover uses image innovation; identical crossing targets may still be confused. The **Analysis** experiments run isolated four-detector comparison, 20-case stress matrix, and known 5 px injection; they do not disturb the current run. **Export evidence** freezes the current report; **Query frames** searches that exported indexed SQLite snapshot. The report ZIP downloads the last export (or creates one if none exists).

On **Video benchmark**, upload MP4/MOV/AVI (150 MB max). Pause, step and seek to inspect frames; seeking starts a new benchmark segment and clears previous measurements. Load the matching zero-based CSV **after** the video for measured accuracy. The camera cannot physically actuate prerecorded frames; the relevant accuracy threshold is centroid RMSE. The **Algorithm lab** exposes current score contributions, not a trained neural-network explanation. The QR points to the current browser host. The local API and WebSocket have no authentication: do not expose them on untrusted networks.

## 4. Desktop controls

Use the six-page left rail (Overview, Live tracking, Scenarios, Video benchmark, Analysis & reports, Algorithm lab). The same Engine object remains active when switching pages. On Live tracking, choose a scenario/detector/controller; open the tabbed Settings dialog for world, target, camera, link and environment controls. The Link tab enables light-travel point-ahead compensation and sets its assumed distance. Pause/Resume (Replay once the run completes), Reset, Open video, Webcam (local device), Load truth CSV, Record MP4, Export report and Screenshot are at the bottom. The **Tools** menu opens the detector arena, X-Ray score inspector, stress suite, sensitivity analyzer, sample-MP4 replay viewer, achievements, tutorial, guided demo, compliance, link and telemetry panels. Press **Space** to return to automatic lock; **WASD/arrow keys** enter manual pan/tilt and command maximum signed motor speed while pressed. Releasing a key stops the motor. These keys work while the main window has keyboard focus.

## 5. Input/output contracts

Ground truth uses a zero-based frame number in the original video coordinates:

```csv
frame,timestamp_s,gt_x,gt_y,visible
0,0.0000,321.5,202.0,1
1,0.0333,322.1,202.4,1
```

Bundled `assets/sample_beacon.mp4` and `.csv` form a matched example. Example command:

```bash
python main.py --video assets/sample_beacon.mp4 --ground-truth assets/sample_beacon.csv --headless --frames 120
```

`frames.csv` contains frame/time/source/ground truth/detection/filter/confidence/visibility/lock/error/pan/tilt/processing/noise/atmosphere fields and `link_quality`. The saved config and seed allow a repeat run. Video without CSV has `null` accuracy, not zero error. The external-video accuracy gate is **centroid RMSE ≤10 px** because the physical camera cannot be steered after recording. Simulator accuracy uses **pointing RMSE ≤10 px**.

## 6. API reference (trusted local network only)

`GET /api/state` full metrics and scenario; `GET /ws` WebSocket-upgraded JSON metrics stream (REST polling fallback); `GET /api/qr.png` dashboard-host QR PNG; `GET /api/plugins` discovered trusted example plugins; `GET /api/frame` JPEG; `GET /api/presets`; `POST /api/control` with `{"action":"pause|start|reset|step|seek|export|record_start|record_stop|xray"}` (`seek` also needs `frame`); `POST /api/scenario` with `id`; `POST /api/config` partial scenario sections; `POST /api/video` binary video with `X-Extension: .mp4`; `POST /api/ground-truth` with `{"csv":"..."}`; `POST /api/compare`, `/api/stress`, `/api/validate`; `POST /target/change` with image-space `x,y` designates a CV candidate; `GET /api/query?min_error=10&metric=pointing` queries indexed evidence; `GET /api/report.zip` downloads the last export. Convenience `GET /metrics`, `GET /frame`, `POST /simulation/start` and `/simulation/stop` are also supported. Browser telemetry streams over a local WebSocket every 250 ms and falls back to JSON polling if the connection closes. `POST /api/config` accepts `detector` and `controller`, including the bundled `plugin:` names.

## 7. Expanded research controls (v0.5)

**Browser Scenarios:** preset library, save/import/export scenario JSON, seeded random generator, startup-default save/reset, PID gains, Kalman/search in desktop Settings, manual assist, zoom/acceleration and experimental FPA/thermal/spoof toggles. Changes to active config restart the seeded run; saved default resides at `<output>/default_scenario.json` and is read on launch unless `--scenario` is specified. Thermal reference calibration is available through `POST /api/control` with `{"action":"calibrate"}` while in simulator mode.

**Browser Live tracking:** click Manual override, then hold arrow buttons or WASD/arrow keys; Auto-lock returns to PID. The manual assist fraction in Scenarios blends your command with detected-target PID output; when a target is missing, the manual command remains in effect. Modelled BER and data volume are **not measured** optical throughput. Analysis includes a non-ML warning rule and an on-demand fixed-camera baseline. Engineering includes the labelled 55-item audit, SGP4 look-angle calculator for a **user-supplied current TLE** and an illustrative world-plane station coverage exercise.

**Python automation:** `from vcapat.api.client import Client; c=Client(); print(c.state())`. The server has no authentication, so restrict it to trusted networks. `python main.py --demo-video 180` produces a silent three-minute scenario montage; it does not add music or certify a pass. Browse the complete [feature audit](Feature_55_Audit.md) before making claims.

**Additional REST:** `GET /api/features`, `/api/leaderboard`, `/api/raw-frame`, `/api/config/export`, `/api/experiment.zip?id=experiment_...`; `POST /api/scenario/save`, `/api/scenario/import`, `/api/scenario/random`, `/api/default/save`, `/api/default/reset`, `/api/sensitivity`, `/api/weakness`, `/api/baseline`, `/api/network`, `/api/tle`. Inputs are validated. In Qt the File menu saves/loads JSON and defaults; Help opens the feature audit.

## 8. Troubleshooting

- **Qt library missing on Linux:** install your distribution's Qt/xkbcommon runtime libraries, or run `--web`; installing PySide6 alone does not provide every system library.
- **No video frames:** check codec support in the installed OpenCV build; try the bundled MP4 first.
- **Benchmark reports N/A:** check that the truth CSV matches the video and uses zero-based frame IDs.
- **No lock in fog/noise:** reduce noise or increase beacon brightness/size; failures are intentional evidence.
- **Camera loses target:** a narrow Kalman-guided search is implemented, but recovery from long occlusions is not guaranteed.
- **No QR PNG:** install `qrcode[pil]` via `requirements.txt`; check that the Host header is valid.
- **Optional ONNX/RL unavailable:** weights are not bundled; check `assets/models/README.md` and the plugin guide.
- **Remote browser unavailable:** pass `--host 0.0.0.0`; confirm local firewall/network access. Do not publish the unauthenticated API to the internet.
