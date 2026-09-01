# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

block_cipher = None

# 项目根目录（SPECPATH 是 PyInstaller 传入的 spec 文件所在目录，比 Path.cwd() 更可靠）
PROJECT_DIR = Path(SPECPATH)

# 关键：把项目根目录加进 sys.path，否则通过 pyinstaller 命令行入口打包时，
# 项目不在 sys.path 上，collect_submodules('game_engine.dialogue') 会静默返回空列表，
# 导致所有口上子模块（laffey/javelin/Z23/ayanami）漏打进包，运行时报
# ModuleNotFoundError: No module named 'game_engine.dialogue.javelin'。
sys.path.insert(0, str(PROJECT_DIR))

# 需要打包的静态资源数据（源路径, 目标文件夹）
datas = [
    (str(PROJECT_DIR / 'frontend'), 'frontend'),
    (str(PROJECT_DIR / 'data'), 'data'),
]

# 隐式导入项（pywebview 及其 Windows 渲染后端）
from PyInstaller.utils.hooks import collect_submodules
hiddenimports = [
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr',
] + collect_submodules('game_engine.dialogue')

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
