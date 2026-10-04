# V-CAPAT PRO v1.1.0 - Project Tree

```text
vcapat-pro/
|-- main.py
|-- validate_mvp.py
|-- requirements.txt
|-- requirements-web.txt
|-- README.md
|-- run_windows.bat
|-- run_linux_macos.sh
|-- build.bat                     # verified onedir Windows release
|-- build_onefile.bat             # verified single-file Windows release
|-- build_release.bat             # builds both formats
|-- build_release.ps1             # full test/validation/build/smoke/package gate
|-- VCAPAT_PRO.spec
|-- VCAPAT_PRO_onefile.spec
|-- build/
|   `-- version_info.txt
|-- scripts/
|   `-- verify_release.py
|-- .github/workflows/
|   `-- windows-release.yml
|-- assets/
|   |-- icon.ico
|   |-- logo.png
|   |-- splash.png
|   |-- desktop_preview.png
|   |-- sample_beacon.mp4
|   `-- sample_beacon.csv
|-- scenarios/
|   |-- ps_compliant_reference.json
|   |-- easy_clear_circular.json
|   |-- emergency_maneuver.json
|   |-- medium_foggy_figure8.json
|   `-- ... additional stress/demo scenarios
|-- docs/
|   |-- VCAPAT_PRO_Technical_Report_v1.1.pdf
|   |-- VCAPAT_PRO_Technical_Report_v1.1.docx
|   |-- Deployment_Guide.md
|   |-- Release_Checklist.md
|   |-- Release_Notes_v1.1.md
|   |-- Validation_Results_v1.1.md
|   |-- PS_Compliance_Matrix.md
|   |-- User_Manual.md
|   `-- ... supporting audit/developer documentation
|-- plugins/
|   |-- example_detector_plugin.py
|   `-- example_controller_plugin.py
|-- tests/                         # 31 automated source tests
`-- vcapat/
    |-- api/                       # REST, WebSocket and six-page browser UI
    |-- config/                    # validated scenario/config + PS compliance
    |-- control/                   # PID, search, point-ahead, manual/RL adapters
    |-- core/                      # shared engine, state machine, feature registry
    |-- detection/                 # CV arena, centroiding, TinyML, XAI, YOLO adapter
    |-- disturbance/               # noise, atmosphere, jitter, platform/sensor models
    |-- gui/                       # PySide6 desktop application
    |-- io/                        # video, webcam, ground truth, TLE, recording
    |-- link/                      # link-quality/BER/network proxies
    |-- metrics/                   # collector, compliance, PDF/CSV/SQLite reports
    |-- plugins/                   # trusted extension loader/interfaces
    |-- security/                  # spoof-robustness helper
    |-- simulation/                # world, camera, target, trajectories, occlusion
    |-- stress/                    # stress, sensitivity and weak-case experiments
    |-- tracking/                  # Kalman, association, multi-target/handover
    `-- utils/                     # geometry, math, QR, runtime resource paths
```

The trained YOLO beacon weight file is intentionally not fabricated or bundled. The default `ai_auto` path uses the self-contained TinyML-assisted candidate ranker plus explainable classical computer vision.
