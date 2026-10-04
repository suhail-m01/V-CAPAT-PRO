# Validation Snapshot

Validation executed in the build workspace on 2026-10-02.

- `python -m pytest -q -k 'not ground_station_sgp4_and_demo_video'`: **30 passed, 1 deselected**. The deselected test requires the `sgp4` package; it is declared in `requirements.txt`, but the isolated build workspace could not download it. The Windows build script installs requirements before running the full suite.
- `python validate_mvp.py`: all static PS compliance checks passed; 120-frame reference smoke test reached LOCKED for 118 frames.
- 180-frame PS reference headless run: completed in `LOCKED` state and generated CSV/JSON/SQLite/PNG/PDF evidence.
- Bundled labelled `sample_beacon.mp4` benchmark (120 frames): acquisition 0.10 s, centroid RMSE 0.121 px, target loss 1.67%, lock retention 98.33%, pipeline average 349.37 FPS in this workspace. Re-acquisition was N/A because no completed loss/recovery event occurred.

Processing FPS is machine-dependent and these figures are development evidence, not certification.
