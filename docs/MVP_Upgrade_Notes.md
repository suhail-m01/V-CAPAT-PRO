# MVP Upgrade Notes — v1.0.0

This revision closes the main gaps identified during the PS-to-code audit.

- Tightened world minimum to 2000×2000, camera rate to ≥30 Hz, and pan/tilt speed to 5–10°/s.
- Added independent target width/height (5–20 px), canonical 10×10 square reference beacon, and seeded-random initial placement in the reference mission.
- Added user-adjustable atmospheric contrast and brightness controls.
- Added a true per-frame platform-motion clamp capped at ±20 px/frame.
- Fixed the blinking-target time-variable defect.
- Added self-contained TinyML logistic candidate classifier and `ai_auto` fusion mode.
- Added explicit PS compliance checker and canonical PS reference scenario.
- Added Windows run/build/onefile scripts, Docker web deployment, health check, deployment guide and acceptance validator.
- Added tests for PS compliance, AI ranking, rectangular targets and blink execution.
- Added a SIH technical report and PS compliance matrix.

The Windows `.exe` is intentionally not shipped from this Linux build workspace; build scripts create it on Windows after tests and MVP validation pass.
