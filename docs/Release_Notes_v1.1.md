# V-CAPAT PRO v1.1.0 Release Notes

## Submission-critical upgrades

1. **Formal technical report**
   - Added 14-page `VCAPAT_PRO_Technical_Report_v1.1.pdf`.
   - Added editable DOCX source.
   - Covers all mandatory report topics and includes requirement traceability, architecture and measured evidence.

2. **Standalone Windows release engineering**
   - Added dedicated onedir and onefile PyInstaller spec files.
   - Added Windows file-version metadata.
   - Added `build_release.ps1` and `build_release.bat`.
   - Added post-build `VCAPAT_PRO.exe --self-test` verification.
   - Added release ZIP creation and SHA-256 checksums.
   - Added Windows GitHub Actions build workflow.
   - Added `scripts/verify_release.py`.
   - Centralized source/frozen resource resolution in `vcapat/utils/paths.py`.

3. **Final readiness fixes**
   - Browser detector selector now exposes `ai_auto` and `tinyml`.
   - Source validation now checks mandatory report and release assets.
   - Automated suite passes 31 tests even when the optional TLE dependency is absent in a non-release development environment; the Windows release gate explicitly requires and verifies SGP4 before packaging.

## Important release boundary

The source tree is prepared to produce and verify the mandatory Windows executable. A real `.exe` must be generated on Windows or the included Windows CI runner; a Linux-generated source ZIP must not be presented as the standalone Windows binary.
