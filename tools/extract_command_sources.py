"""Extract raw SOURCE values from TW COMF*.ERB files into command_effects.toml."""

from __future__ import annotations

import re
from pathlib import Path

# erAL index → TW COMF number (when they differ)
INDEX_MAP = {
    14: 15,    # 阴蒂爱抚
    15: 19,    # 接吻(继续)
    97: 108,   # 打胸部
    100: 120,  # 强制舔阴
    101: 121,  # 磨镜
    102: 125,  # 被爱抚
    103: 126,  # 互揉胸部
    104: 127,  # 被放入A珠
    110: 130,  # 被正常位
    111: 131,  # 被后背位
    112: 132,  # 被对面座位
    113: 133,  # 被背面座位
}

# TW SOURCE name → erAL index
NAME_MAP = {
    "快Ｃ": 0,
    "快Ｖ": 1,
    "快Ａ": 2,
    "快Ｂ": 3,
    "快Ｍ": 4,
    "液体": 9,
    "潤滑": 9,
    "情愛": 10,
    "性行動": 11,
    "達成": 12,
    "苦痛": 13,
    "恐怖": 14,
    "欲情": 15,
    "恭順": 16,
    "露出": 17,
    "屈従": 18,
    "歓楽": 20,
    "征服": 21,
    "受動": 22,
    "不潔": 30,
    "鬱屈": 31,
    "逸脱": 32,
    "反感": 33,
    "誘惑": 50,
    "侮辱": 51,
    "挑発": 52,
    "奉仕": 53,
    "強求": 54,
    "加虐": 55,
}

# Match order: try pure number first, then base-value extraction from expressions
SOURCE_RE = re.compile(
    r"SOURCE:(PLAYER:)?([^\s=]+)\s*(\+)?=\s*(.+)$"
)


def extract_base_value(expr: str) -> int | None:
    """Extract a base integer from the right-hand side of a SOURCE assignment.

    Preference order:
    1. Pure number: 40, 100
    2. Leading number with +: 100 + GET_REVISION(...)
    3. Trailing + number: ABL:X * 3 + 20
    """
    expr = expr.strip()
    # 1. Pure number
    if re.fullmatch(r"\d+", expr):
        return int(expr)
    # 2. Leading number followed by operator
    m = re.match(r"(\d+)\s*[-+*/&|]", expr)
    if m:
        return int(m.group(1))
    return None


def extract_from_file(path: Path) -> tuple[dict[int, int], dict[int, int], list[str]]:
    """Return (target_source, player_source, unmapped_names)."""
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    # Find @COM{N} line (avoid @COM60_DEFINITION, @COM60_DISPLAY etc.)
    com_start = -1
    for i, line in enumerate(lines):
        if re.match(r"@COM\d+($|\s)", line.strip()):
            com_start = i
            break

    if com_start < 0:
        return {}, {}, []

    # Gather lines until next @-prefixed definition or EOF
    block_lines = []
    for line in lines[com_start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("@") and not stripped.startswith("@_"):
            break
        block_lines.append(stripped)

    # Separate = and += values; = takes priority over +=.
    target_eq: dict[int, int] = {}
    target_plus: dict[int, int] = {}
    player_eq: dict[int, int] = {}
    player_plus: dict[int, int] = {}
    unmapped: set[str] = set()

    for line in block_lines:
        # Skip TIMES and reassignment of the form SOURCE:X = SOURCE:X * ...
        if line.startswith("TIMES SOURCE:"):
            continue
        if re.match(r"SOURCE:[^=]+=\s*SOURCE:", line):
            continue

        m = SOURCE_RE.match(line)
        if not m:
            continue

        is_player = m.group(1) is not None
        name = m.group(2)
        op = m.group(3)
        expr = m.group(4)

        # For +=, only accept if RHS is a bare number (not ABL*X)
        if op == "+" and not re.fullmatch(r"\s*\d+\s*", expr):
            continue

        idx = NAME_MAP.get(name)
        if idx is None:
            if not name.startswith(("_", "TEMP", "LOCAL", "ARG")):
                unmapped.add(name)
            continue

        value = extract_base_value(expr)
        if value is None:
            continue

        if is_player:
            if idx in (0, 1, 2, 3, 4):
                idx = idx + 40
            dest_eq = player_eq
            dest_plus = player_plus
        else:
            dest_eq = target_eq
            dest_plus = target_plus

        if op is None:
            # = assignment: non-zero values take priority; don't let a
            # conditional zero-clear overwrite a previously-seen base value.
            if value != 0 or idx not in dest_eq:
                dest_eq[idx] = value
        else:
            dest_plus[idx] = value

    # Merge: = values win over += values; ignore 0 from conditional branches
    # if a non-zero value exists elsewhere for the same SOURCE.
    target: dict[int, int] = {}
    for idx in set(target_eq) | set(target_plus):
        v = target_eq.get(idx, target_plus.get(idx, 0))
        # Drop conditional zero-clears when a non-zero base exists
        if v == 0 and (target_eq.get(idx) is not None or target_plus.get(idx) is not None):
            non_zero = [x for x in (target_eq.get(idx), target_plus.get(idx)) if x is not None and x != 0]
            if non_zero:
                v = non_zero[-1]
        target[idx] = v

    player: dict[int, int] = {}
    for idx in set(player_eq) | set(player_plus):
        v = player_eq.get(idx, player_plus.get(idx, 0))
        if v == 0 and (player_eq.get(idx) is not None or player_plus.get(idx) is not None):
            non_zero = [x for x in (player_eq.get(idx), player_plus.get(idx)) if x is not None and x != 0]
            if non_zero:
                v = non_zero[-1]
        player[idx] = v

    return target, player, sorted(unmapped)


def main() -> None:
    tw_comf_dir = Path("../eratw4.980-260320-SUNNY(PC)/ERB/コマンド関連/COMF/")
    output_path = Path("data/base/effects/command_effects.toml")
    train_path = Path("data/base/commands/train.toml")

    train_text = train_path.read_text(encoding="utf-8")
    valid_indices = {int(m.group(1)) for m in re.finditer(r"index = (\d+)", train_text)}

    # Build lookup: TW COMF number -> file path
    tw_files: dict[int, Path] = {}
    for f in tw_comf_dir.glob("COMF*.ERB"):
        m = re.match(r"COMF(\d+)", f.name)
        if m:
            tw_files[int(m.group(1))] = f

    effects: list[tuple[int, dict[int, int], dict[int, int]]] = []
    all_unmapped: set[str] = set()
    processed = 0
    empty = 0
    no_tw_file = 0

    for cmd_index in sorted(valid_indices):
        tw_index = INDEX_MAP.get(cmd_index, cmd_index)
        f = tw_files.get(tw_index)
        if f is None:
            no_tw_file += 1
            continue

        target, player, unmapped = extract_from_file(f)
        all_unmapped.update(unmapped)

        if not target and not player:
            empty += 1
            continue

        effects.append((cmd_index, target, player))
        processed += 1

    # Write TOML
    lines = [
        '# 指令原始 SOURCE 定义',
        '# command_index: 引用 train.toml 的 index',
        '# target_source: 对目标角色产生的原始 SOURCE（整数索引 -> 值）',
        '# player_source: 对玩家产生的原始 SOURCE（整数索引 -> 值）',
        '# 受方快感组 0-4, 施方反馈组 40-44',
        '',
    ]

    for cmd_index, target, player in sorted(effects):
        lines.append("[[effect]]")
        lines.append(f"command_index = {cmd_index}")
        if target:
            pairs = ", ".join(f"{k} = {v}" for k, v in sorted(target.items()))
            lines.append(f"target_source = {{{pairs}}}")
        if player:
            pairs = ", ".join(f"{k} = {v}" for k, v in sorted(player.items()))
            lines.append(f"player_source = {{{pairs}}}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    missing = sorted(valid_indices - {e[0] for e in effects})
    print(f"Processed {processed} files with SOURCE data, {empty} empty.")
    print(f"No TW file for {no_tw_file} commands.")
    print(f"Wrote {len(effects)} effects to {output_path}")
    print(f"Missing in train.toml ({len(missing)} commands): {missing}")
    if all_unmapped:
        print(f"Unmapped SOURCE names ({len(all_unmapped)}): {', '.join(sorted(all_unmapped))}")


if __name__ == "__main__":
    main()
