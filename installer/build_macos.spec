# build_macos.spec — PyInstaller spec for macOS
#
# Produces:  installer/dist/EDA Report.app
# Tested on: macOS 13+ with no Python installed
#
# After building, sign with:
#   codesign --deep --sign - 'installer/dist/EDA Report.app'
# Or with a Developer ID (if available):
#   codesign --deep --sign "Developer ID Application: ..." 'installer/dist/EDA Report.app'
#
# Without signing, users must right-click → Open to bypass Gatekeeper on first run.
# Document this in the README for non-technical collaborators.

import sys
import pathlib

ROOT = pathlib.Path(SPECPATH).parent  # repo root

block_cipher = None

a = Analysis(
    [str(ROOT / 'launcher' / 'app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'installer' / 'quarto'), 'quarto'),
        (str(ROOT / 'eda_report.qmd'), '.'),
        (str(ROOT / 'eda'), 'eda'),
        (str(ROOT / 'launcher' / 'templates'), 'launcher/templates'),
        (str(ROOT / 'launcher' / 'static'),    'launcher/static'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'plotnine',
        'mizani',
        'pyreadstat',
        'great_tables',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test', 'unittest'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EDA Report',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    argv_emulation=True,    # required for macOS .app double-click behavior
    # TODO: set icon=str(ROOT / 'installer' / 'icon.icns') when icon is available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EDA Report',
)

app = BUNDLE(
    coll,
    name='EDA Report.app',
    # TODO: set icon=str(ROOT / 'installer' / 'icon.icns') when icon is available
    bundle_identifier='org.ccf.hvti.eda-report',
    info_plist={
        'CFBundleShortVersionString': '0.1.0',
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
    },
)
