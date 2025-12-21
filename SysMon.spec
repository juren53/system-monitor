# -*- mode: python ; coding: utf-8 -*-
"""
SysMon PyInstaller Specification
Version: v0.2.0
Release: 2025-12-21
"""

a = Analysis(
    ['src\\sysmon.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons\\ICON_SysMon-t.png', 'icons'),
        ('icons\\ICON_sysmon.png', 'icons'),
        ('icons\\ICON_sysmon.ico', 'icons'),
    ],
    hiddenimports=['matplotlib.backends.qt_compat'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SysMon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons\\ICON_SysMon-t.png',
)
