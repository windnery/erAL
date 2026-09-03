"""地图字符画校验脚本：验证 lines 每行显示宽度一致、tokens 记号都出现在画中。

用法：
    python tools/check_map_art.py
显示宽度规则：East Asian Width 为 W/F 的字符占 2 单元（全角），其余占 1（半角）。
行尾的全角空格会被忽略（对渲染无影响）。
"""
import json
import sys
import unicodedata
from pathlib import Path

MAPS_DIR = Path(__file__).parent.parent / 'data' / 'maps'

# 控制台非 UTF-8（如 GBK）时字符画包含 ■ 等符号会崩，降级输出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def char_width(ch: str) -> int:
    return 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1


def display_width(line: str) -> int:
    return sum(char_width(c) for c in line.rstrip('　'))


def is_box_row(line: str) -> bool:
    """盒子行：以边框字符开头且结尾（顶/中/底边框与带两墙的内容行）"""
    box_chars = '┌├└│'
    right_chars = '┐┤┘│'
    return (
        len(line) >= 2
        and line[0] in box_chars
        and line[-1] in right_chars
    )


def main():
    ok = True
    for json_file in sorted(MAPS_DIR.glob('*.json')):
        if json_file.name.startswith('_'):
            continue
        data = json.loads(json_file.read_text('utf-8'))
        lines = data.get('lines')
        if not lines:
            continue
        region = json_file.stem
        art = ''.join(lines)
        box_widths = set()
        for i, line in enumerate(lines):
            width = display_width(line)
            print(f'{region} L{i:02d} w={width:3d} |{line}|')
            if is_box_row(line):
                box_widths.add(width)
        if len(box_widths) > 1:
            ok = False
            print(f'[FAIL] {region}: 盒子行宽不一致 {sorted(box_widths)}')
        for token, meta in data.get('tokens', {}).items():
            if f'[{token}]' not in art:
                ok = False
                print(f'[FAIL] {region}: 记号 [{token}] 未出现在字符画中（记号约定为方括号包裹）')
            if not (meta.get('exit') or meta.get('node')):
                ok = False
                print(f'[FAIL] {region}: 记号 {token} 缺少 node/exit 字段')
    print('ALL OK' if ok else 'HAS ERRORS')
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
