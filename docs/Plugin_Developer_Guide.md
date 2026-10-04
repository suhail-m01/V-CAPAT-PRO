# Trusted local plugin development

Plugins live in `plugins/` and execute as ordinary local Python. **Do not load untrusted plugins.** The loader validates plugin names, discovers the two bundled examples, imports a selected file, and expects `PLUGIN_KIND = 'detector'` or `'controller'` plus `PLUGIN_CLASS = YourClass`.

A detector implements `detect(frame, prediction=None, gate_px=None) -> Detection` (or `(x, y, confidence)`), where the frame is a camera-origin grayscale or BGR NumPy array. Coordinates are in **camera pixels**; confidence is 0–1. `vcapat.detection.base.Detection` can carry bounding box, candidate list and a debug mask. Plugins must not read simulator ground truth. A controller implements `step(error_x_deg, error_y_deg, dt, limit_deg_s) -> (pan_deg_s, tilt_deg_s)`; camera actuation still saturates commands to the configured maximum.

Try the two bundled plugins via Desktop Detector / Controller menus or a scenario JSON:

```json
{
  "detector": "plugin:example_detector_plugin",
  "controller": "plugin:example_controller_plugin"
}
```

Partial scenario JSON also requires a valid scenario name and fields from `vcapat.config.settings.Scenario`; use `Scenario().to_dict()` then edit these keys. The browser configuration offers the bundled plugins. `GET /api/plugins` lists discovered trusted example file names.

Plugins are dynamically loaded by file path; PyInstaller's `build.bat` includes the `plugins/` directory. The example controller is proportional-only; the production default PID includes anti-windup and derivative action. Experiment reports retain selected plugin names in the config snapshot. Plugins are not an isolation boundary and should be reviewed before execution.
