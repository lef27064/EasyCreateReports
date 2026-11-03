# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['core_engine'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pydantic', 'tkinter', 'matplotlib', 'numpy'], # Αποφυγή προβληματικών βιβλιοθηκών κατά το build
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app_gui',
)