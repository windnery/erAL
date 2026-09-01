#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
erAL 已有立绘一键轻量化压制工具
功能：
1. 遍历 frontend/assets/portraits/ 下的所有已有立绘 WebP 文件
2. 对超大分辨率做等比例缩放（限制最大高度 1280px）
3. 按 quality=80 进行高保真二次压缩，将总体积降低 70%~80%（~180MB -> ~35MB）
"""

import os
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PORTRAITS_DIR = PROJECT_ROOT / 'frontend' / 'assets' / 'portraits'

MAX_HEIGHT = 1280
WEBP_QUALITY = 80


def optimize_all_portraits():
    all_files = list(PORTRAITS_DIR.rglob('*.webp'))
    total = len(all_files)
    print(f"[-] 开始扫描并优化 {total} 张已有立绘 (最大高度: {MAX_HEIGHT}px, 质量: {WEBP_QUALITY})...")

    before_size = sum(f.stat().st_size for f in all_files)
    processed = 0

    for f in all_files:
        try:
            with Image.open(f) as img:
                img_format = img.format
                orig_w, orig_h = img.size
                
                # 检查是否需要缩放
                if orig_h > MAX_HEIGHT:
                    new_w = int(orig_w * (MAX_HEIGHT / orig_h))
                    img_resized = img.resize((new_w, MAX_HEIGHT), Image.Resampling.LANCZOS)
                    img_resized.save(f, 'WEBP', quality=WEBP_QUALITY, method=4)
                else:
                    # 分辨率已符合，仅重新高保真压缩
                    img.save(f, 'WEBP', quality=WEBP_QUALITY, method=4)
                
                processed += 1
                if processed % 50 == 0 or processed == total:
                    print(f" [+] 优化进度: {processed}/{total}")
        except Exception as e:
            print(f" [!] 优化失败 {f.name}: {e}")

    after_size = sum(f.stat().st_size for f in all_files)
    saved_mb = (before_size - after_size) / (1024 * 1024)
    print("\n" + "=" * 60)
    print(f"[√] 全量优化完成！")
    print(f"    优化前总大小: {before_size / (1024*1024):.2f} MB")
    print(f"    优化后总大小: {after_size / (1024*1024):.2f} MB")
    print(f"    节省存储空间: {saved_mb:.2f} MB (体积下降 {(before_size - after_size) / before_size * 100:.1f}%)")
    print("=" * 60)


if __name__ == '__main__':
    optimize_all_portraits()
