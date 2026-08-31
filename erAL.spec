# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

block_cipher = None

# 项目根目录
PROJECT_DIR = Path.cwd()

# 需要打包的静态资源数据（源路径, 目标文件夹）
datas = [
    (str(PROJECT_DIR / 'frontend'), 'frontend'),
    (str(PROJECT_DIR / 'data'), 'data'),
]

# 隐式导入项（pywebview 及其 Windows 渲染后端）
hiddenimports = [
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr',
]

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='erAL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 设置为 False 隐藏命令行黑窗口，需要调试时可改为 True
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='erAL',
)
