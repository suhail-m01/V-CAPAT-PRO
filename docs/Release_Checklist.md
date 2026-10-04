# SIH26169 Release Checklist - V-CAPAT PRO v1.1.0

## Mandatory software deliverable
- [ ] Build on Windows 10/11 x64 with Python 3.11 or 3.12.
- [ ] Run `build_release.bat`.
- [ ] Confirm full automated tests pass.
- [ ] Confirm `validate_mvp.py` passes.
- [ ] Confirm packaged `VCAPAT_PRO.exe --self-test` passes.
- [ ] Double-click the final EXE and verify the PySide6 desktop UI.
- [ ] Run a simulator scenario and export a PDF performance report.
- [ ] Run the supplied MP4 benchmark and export evidence.
- [ ] Keep `VCAPAT_PRO_v1.1.0_Windows_x64.zip` as primary release.
- [ ] Keep the onefile ZIP as a secondary convenience build.

## Mandatory documents
- [x] Source code - included and modular.
- [x] Technical report - `docs/VCAPAT_PRO_Technical_Report_v1.1.pdf` (10-15 page target).
- [x] Editable technical report source - `.docx` included.
- [x] User manual source - `docs/User_Manual.md`.
- [x] PS compliance matrix - `docs/PS_Compliance_Matrix.md`.

## Demo safety
- [ ] Demo from local files, not cloud-dependent resources.
- [ ] Disable Windows sleep during presentation.
- [ ] Keep the sample benchmark video and ground-truth CSV locally.
- [ ] Keep the verified onedir package as fallback if onefile startup is slow.
- [ ] Do not claim flight qualification, real optical BER certification or real ISRO dataset training.
