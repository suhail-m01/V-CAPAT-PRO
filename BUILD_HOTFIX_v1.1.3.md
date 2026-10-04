# V-CAPAT PRO v1.1.3 build hotfix

This release hardens the Windows release pipeline.

## Fixes

- Version metadata moved from `build/version_info.txt` to `packaging/version_info.txt` so cleaning `build/` cannot destroy a required PyInstaller input.
- Both PyInstaller specs now read version metadata from the persistent `packaging/` folder.
- Release preflight validates the icon, version metadata, technical report, user manual, compliance matrix, specs, and smoke-test script before packaging.
- Windows archive creation retries if Defender/File Explorer temporarily locks `base_library.zip` or another generated file.
- Any leftover `VCAPAT_PRO.exe` smoke-test process is terminated before copying/compressing release artifacts.
- Generated build directories are cleaned individually rather than deleting source-like metadata.
- Windows UTF-8 test reads are explicit, preventing `cp1252` decode failures in `test_multi_page.py`.
- Python 3.11 x64 is preferred; Python 3.12 x64 remains supported.

Run `build_release.bat` from the project root.
