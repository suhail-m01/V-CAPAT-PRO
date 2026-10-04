# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH)
datas = [
    (str(root / 'assets'), 'assets'),
    (str(root / 'scenarios'), 'scenarios'),
    (str(root / 'docs'), 'docs'),
    (str(root / 'plugins'), 'plugins'),
    (str(root / 'vcapat' / 'api' / 'companion_web'), 'vcapat/api/companion_web'),
]
hiddenimports = collect_submodules('qrcode')
binaries = []
for pkg in ('sgp4',):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    ['main.py'],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VCAPAT_PRO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(root / 'assets' / 'icon.ico'),
    version=str(root / 'packaging' / 'version_info.txt'),
)
