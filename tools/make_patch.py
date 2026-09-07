# -*- coding: utf-8 -*-
"""erAL 增量补丁打包工具 (make_patch.py)

原理：
1. 通过 git diff 自动比对指定旧版本 Tag（默认上一个版本）到当前 HEAD 的全部变动文件；
2. 若涉及 Python 代码/配置变动，自动抓取 dist/erAL/erAL.exe；
3. 若涉及 frontend/ 或 data/ 变动（包括本次新增的字体、未来新增的图片、样式、脚本、地图 JSON），精准抓取对应文件；
4. 排除未变动的文件（特别是未改动的大体积 assets 图片库或未改动的字体）；
5. 打包为 erAL_<版本号>_patch.zip，老玩家解压覆盖即可升级且保留 sav/ 存档。

用法：
    # 自动比对上一个 Tag（例如 v0.1.3-alpha.1）并打包：
    python tools/make_patch.py

    # 手动指定基础版本与目标版本名：
    python tools/make_patch.py v0.1.3-alpha.1 v0.1.4-alpha
"""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

# 保证 Windows 控制台 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist" / "erAL"


def get_last_tag() -> str | None:
    """获取最近的一个 Git Release Tag"""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace").strip()
        return tag if tag else None
    except Exception:
        return None


def get_changed_files(base_ref: str) -> list[str]:
    """通过 git diff 获取自 base_ref 到当前 HEAD 的变动文件"""
    cmd = ["git", "diff", "--name-only", f"{base_ref}..HEAD"]
    out = subprocess.check_output(cmd, cwd=ROOT).decode("utf-8", errors="replace")
    return [line.strip() for line in out.splitlines() if line.strip()]


def make_patch(base_tag: str | None = None, target_name: str | None = None):
    if not DIST_DIR.exists():
        print(f"[-] 错误：未找到构建目录: {DIST_DIR}")
        print("请先执行 `pyinstaller erAL.spec` 构建生成 dist/erAL 产物后再打补丁！")
        return False

    if not base_tag:
        base_tag = get_last_tag()

    if not base_tag:
        print("[-] 未能自动获取上一个版本 Tag，请手动指定，例如: python tools/make_patch.py v0.1.3-alpha.1")
        return False

    print("==================================================")
    print(" [*] erAL 增量补丁打包工具")
    print(f" [*] 基准版本: {base_tag}")
    print(f" [*] 目标版本: {target_name or 'HEAD'}")
    print("==================================================")

    changed_files = get_changed_files(base_tag)
    print(f"\n[+] Git 检测到自 [{base_tag}] 以来共有 {len(changed_files)} 处变动文件。")

    has_py_change = False
    files_to_pack: set[tuple[Path, str]] = set()  # (物理绝对路径, zip内相对路径)
    ignored_count = 0
    missing_in_dist = []

    # 忽略的工程/开发/测试目录及文件
    IGNORE_PREFIXES = ("tests", "docs", "tools", ".github", ".vscode", "logs", "sav", "参考图", "eratohoK", "eratw4")
    IGNORE_NAMES = ("README.md", "plan.txt", ".gitignore", "dev_server.py")

    for path_str in changed_files:
        p = Path(path_str)

        # 1. 忽略测试、工具、文档与开发配置文件
        if p.parts and p.parts[0] in IGNORE_PREFIXES:
            ignored_count += 1
            continue
        if p.name in IGNORE_NAMES:
            ignored_count += 1
            continue

        # 2. Python 逻辑或 Spec 改动 -> 标记需要携带 erAL.exe
        if p.suffix in (".py", ".spec"):
            has_py_change = True
            continue

        # 3. 数据文件变动 -> _internal/data/
        if p.parts and p.parts[0] == "data":
            src = DIST_DIR / "_internal" / p
            if src.exists() and src.is_file():
                files_to_pack.add((src, f"_internal/{p.as_posix()}"))
            else:
                missing_in_dist.append(path_str)
            continue

        # 4. 前端静态资源变动 -> _internal/frontend/
        # 注意：若本次更新新增了字体（如 font/）或立绘（assets/），也会精准收集进补丁
        if p.parts and p.parts[0] == "frontend":
            src = DIST_DIR / "_internal" / p
            if src.exists() and src.is_file():
                files_to_pack.add((src, f"_internal/{p.as_posix()}"))
            else:
                missing_in_dist.append(path_str)
            continue

    # 5. 如果有 Python 改动，将编译后的主程序纳入补丁
    if has_py_change:
        exe_path = DIST_DIR / "erAL.exe"
        if exe_path.exists():
            files_to_pack.add((exe_path, "erAL.exe"))
            print("  [+] 检测到 Python 核心代码更新，已自动纳入: erAL.exe")
        else:
            print(f"  [!] 警告：检测到 Python 改动，但未在 {DIST_DIR} 找到 erAL.exe！")

    if not files_to_pack:
        print("[!] 未找到任何需要打包的增量文件（所有变动可能均为文档或测试用例）。")
        return False

    # 补丁包文件名
    ver_label = target_name or "latest"
    patch_filename = f"erAL_{ver_label}_patch.zip"
    out_zip = ROOT / "dist" / patch_filename

    print(f"\n[*] 正在写入增量压缩包: {out_zip.name} ...")
    uncompressed_total = 0
    font_detected = False

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_path, arcname in sorted(files_to_pack, key=lambda x: x[1]):
            zf.write(src_path, arcname)
            sz = src_path.stat().st_size
            uncompressed_total += sz
            sz_str = f"{sz / 1024:.1f} KB" if sz < 1024 * 1024 else f"{sz / (1024*1024):.2f} MB"
            print(f"  + [{sz_str:>9}] {arcname}")
            if "font" in arcname:
                font_detected = True

    compressed_size = out_zip.stat().st_size
    compressed_mb = compressed_size / (1024 * 1024)
    uncompressed_mb = uncompressed_total / (1024 * 1024)

    print("\n==================================================")
    print(" [OK] 增量补丁打包成功！")
    print(f" [*] 补丁文件: {out_zip}")
    print(f" [*] 文件总数: {len(files_to_pack)} 个 (已跳过开发/测试文件 {ignored_count} 处)")
    if font_detected:
        print(" [*] 包含新增字体: 是 (更纱黑体等宽字体已随本次增量打入)")
    print(f" [*] 原始体积: {uncompressed_mb:.2f} MB")
    print(f" [*] 压缩后体积: {compressed_mb:.2f} MB (较完整包大幅精简！)")
    print("==================================================")
    print("提示：玩家只需将补丁压缩包内的文件直接解压覆盖到原有游戏根目录即可。")
    return True


def main():
    parser = argparse.ArgumentParser(description="erAL 增量补丁一键打包工具")
    parser.add_argument("base_tag", nargs="?", default=None, help="基准版本 Tag（如 v0.1.3-alpha.1），默认自动读取最近 Tag")
    parser.add_argument("target_name", nargs="?", default=None, help="目标版本标识（如 v0.1.4-alpha），用于命名补丁包")
    args = parser.parse_args()

    make_patch(base_tag=args.base_tag, target_name=args.target_name)


if __name__ == "__main__":
    main()
