# build_windows.spec — PyInstaller spec for Windows
#
# Produces:  installer/dist/EDA Report.exe
# Tested on: Windows 10/11 with no Python installed
#
# Prerequisites
# -------------
# - Place the Quarto Windows standalone binary at installer/quarto/
#   (see installer/build.sh for instructions)

import sys
import pathlib

ROOT = pathlib.Path(SPECPATH).parent  # repo root

block_cipher = None

a = Analysis(
    [str(ROOT / 'launcher' / 'app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle the Quarto binary
        (str(ROOT / 'installer' / 'quarto'), 'quarto'),
        # Bundle the Quarto report template and eda package
        (str(ROOT / 'eda_report.qmd'), '.'),
        (str(ROOT / 'eda'), 'eda'),
        # Bundle the web UI templates and static files
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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EDA Report',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window — browser-based UI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # TODO: set icon=str(ROOT / 'installer' / 'icon.ico') when icon is available
)
