"""口上覆盖率与 action 契约漂移检查。

用法：
    python tools/check_dialogue_coverage.py

检查三件事：
1. **契约漂移**：扫描代码中 ``say_chara_line`` / ``get_scene`` 的字面量 action，
   与 ``ACTION_CONTRACT`` 交叉比对。
   - 代码在用但契约未登记  -> ERROR（新增指令忘了登记 action）
   - 契约有但代码从未字面调用 -> WARNING（可能为动态派发，需人工确认）
   - 契约 ``source`` 文件不存在 -> ERROR（契约陈旧）
2. **json 数据校验**：``data/dialogue/*.json`` 的 ``when`` 键必须在词汇表内、
   条目结构合法（``variants`` 为场景列表）。
3. **角色覆盖率**：每个已有口上来源（json / Python 模块）的角色，对照契约列出
   缺失 action 与覆盖率；并报告目标角色是否已建立口上来源。

退出码：存在 ERROR 时返回 1，否则 0。
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.dialogue_config import ACTION_CONTRACT  # noqa: E402
from game_engine.dialogue import (  # noqa: E402
    get_available_actions,
    known_chara_ids,
)
from game_engine.dialogue._resolver import KNOWN_WHEN_KEYS, DATA_DIR  # noqa: E402

SCAN_DIRS = ("game_engine", "events", "managers")
CALL_NAMES = ("say_chara_line", "get_scene")

# 第一批口上目标角色（见 docs/roadmap.md §2.1）
TARGET_ROSTER = (
    "javelin", "laffey", "z23", "ayanami",
    "illustrious", "enterprise", "akagi", "unicorn",
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def scan_literal_actions() -> dict[str, set[str]]:
    """AST 扫描代码中传给 say_chara_line/get_scene 的字面量 action。"""
    found: dict[str, set[str]] = {}
    for sub in SCAN_DIRS:
        base = ROOT / sub
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                    continue
                if node.func.id not in CALL_NAMES:
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.setdefault(arg.value, set()).add(
                            str(path.relative_to(ROOT))
                        )
    return found


def check_contract_drift(used: dict[str, set[str]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for action, files in sorted(used.items()):
        if action not in ACTION_CONTRACT:
            errors.append(
                f"action 未登记：'{action}' 被 {', '.join(sorted(files))} 使用，"
                f"但不在 ACTION_CONTRACT"
            )

    for action, spec in ACTION_CONTRACT.items():
        if action not in used:
            warnings.append(f"契约 action '{action}' 从未被字面调用（可能为动态派发）")
        source = spec.get("source")
        if source and not (ROOT / "game_engine" / source).exists():
            errors.append(f"契约 action '{action}' 的 source 不存在：{source}")

    return errors, warnings


def check_json_files() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not DATA_DIR.exists():
        return errors, warnings

    for path in sorted(DATA_DIR.glob("*.json")):
        rel = path.relative_to(ROOT)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: JSON 解析失败：{exc}")
            continue
        actions = data.get("actions")
        if not isinstance(actions, dict):
            errors.append(f"{rel}: 缺少 'actions' 字典")
            continue
        for action, entries in actions.items():
            if action not in ACTION_CONTRACT:
                errors.append(f"{rel}: action '{action}' 未登记在 ACTION_CONTRACT")
            if not isinstance(entries, list):
                errors.append(f"{rel}: action '{action}' 条目应为列表")
                continue
            for i, entry in enumerate(entries):
                loc = f"{rel}: action '{action}' 第 {i} 条"
                if not isinstance(entry, dict):
                    errors.append(f"{loc} 应为对象")
                    continue
                variants = entry.get("variants")
                if (
                    not isinstance(variants, list)
                    or not variants
                    or not all(
                        isinstance(scene, list)
                        and all(isinstance(m, str) for m in scene)
                        for scene in variants
                    )
                ):
                    errors.append(f"{loc} 的 'variants' 必须是「字符串列表的列表」")
                when = entry.get("when")
                if when is not None:
                    if not isinstance(when, dict):
                        errors.append(f"{loc} 的 'when' 应为对象")
                        continue
                    for key in when:
                        if key not in KNOWN_WHEN_KEYS:
                            errors.append(f"{loc} 的 when 键 '{key}' 不在词汇表中")
    return errors, warnings


def report_coverage() -> None:
    print("=" * 68)
    print("角色口上覆盖率（对照 ACTION_CONTRACT，共 %d 个 action）" % len(ACTION_CONTRACT))
    print("=" * 68)
    ids = sorted(known_chara_ids())
    if not ids:
        print("（尚无任何 json 或 Python 口上来源）")
    for chara_id in ids:
        available = get_available_actions(chara_id)
        missing = [a for a in ACTION_CONTRACT if a not in available]
        pct = 100 * len(available) / len(ACTION_CONTRACT)
        print(f"\n[{chara_id}]  {len(available)}/{len(ACTION_CONTRACT)}  ({pct:.0f}%)")
        if missing:
            print("  缺失: " + ", ".join(missing))
        else:
            print("  已全覆盖")

    print("\n" + "=" * 68)
    print("目标角色来源状态")
    print("=" * 68)
    for chara_id in TARGET_ROSTER:
        has = "有" if chara_id in ids else "无"
        print(f"  {chara_id:<12} {has}口上来源")


def main() -> int:
    used = scan_literal_actions()
    errors, warnings = check_contract_drift(used)
    json_errors, json_warnings = check_json_files()
    errors.extend(json_errors)
    warnings.extend(json_warnings)

    report_coverage()

    print("\n" + "=" * 68)
    print("契约漂移")
    print("=" * 68)
    if errors:
        print(f"\nERROR ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\nWARNING ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("无漂移，契约与代码一致。")

    print()
    if errors:
        print(f"检查失败：{len(errors)} 个 ERROR。")
        return 1
    print("检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
