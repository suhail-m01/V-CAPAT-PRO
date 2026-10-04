# V-CAPAT PRO v1.1 Validation Results

Validation date: 02 October 2026.

## Source acceptance gate

- Automated tests: **31 passed** in the source validation environment.
- `validate_mvp.py`: **PASS** for all static PS constraints, mandatory report/release assets, browser AI detector exposure and 120-frame tracking smoke test.
- Source `--self-test`: **PASS**, 60 frames processed, final state `LOCKED`, CSV/JSON/PDF evidence exported.

The Windows release script performs a stricter dependency import gate including `sgp4`, then repeats tests and validation before packaging. The actual Windows PE executable must be built and smoke-tested on Windows or the included Windows GitHub Actions runner.

## Representative deterministic runs

### Easy - Clear Orbit

- Acquisition: 0.10 s
- Pointing RMSE: 5.724 px
- Target loss: 0.67%
- Lock retention: 99.33%
- Average processing: 407.08 FPS
- Re-acquisition: N/A because no measured loss event occurred

### Emergency Maneuver

- Acquisition: 0.10 s
- Pointing RMSE: 9.323 px
- Target loss: 0.74%
- Maximum re-acquisition: 0.867 s
- Lock retention: 99.26%
- Average processing: 83.36 FPS
- All five measured PS performance checks: PASS

### Labelled sample MP4

- Acquisition: 0.10 s
- Centroid RMSE: 0.121 px
- Target loss: 1.67%
- Lock retention: 98.33%
- Average processing: 353.91 FPS
- Re-acquisition: N/A because no measured loss/recovery event occurred

## Interpretation

These are representative development-environment measurements from deterministic bundled scenarios/sample data. They are not guaranteed on other hardware and are not flight-qualification or ISRO certification results. Final SIH submission evidence should be regenerated from the exact Windows executable used during the demonstration.
