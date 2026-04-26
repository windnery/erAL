"""Command coverage matrix: track which train commands have schema/effect/test coverage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import tomllib


def load_train(path: Path) -> list[dict]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return raw.get("train", [])


def load_effects(path: Path) -> dict[int, dict]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    result: dict[int, dict] = {}
    for item in raw.get("effect", []):
        result[int(item["command_index"])] = item
    return result


def scan_test_references(test_dir: Path) -> set[int]:
    """Crude scan for hard-coded command indices in test files."""
    refs: set[int] = set()
    if not test_dir.exists():
        return refs
    for path in test_dir.glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        # Look for patterns like index = 300, command_index = 0, etc.
        import re
        for m in re.finditer(r"[=:]\s*(\d+)", text):
            val = int(m.group(1))
            if 0 <= val <= 999:
                refs.add(val)
    return refs


def build_matrix(root: Path) -> list[dict]:
    train_path = root / "data" / "base" / "commands" / "train.toml"
    effects_path = root / "data" / "base" / "effects" / "command_effects.toml"
    test_dir = root / "tests"

    train_items = load_train(train_path)
    effects = load_effects(effects_path)
    test_refs = scan_test_references(test_dir)

    rows: list[dict] = []
    for item in train_items:
        idx = int(item["index"])
        effect = effects.get(idx)
        row = {
            "index": idx,
            "label": item.get("label", ""),
            "category_set": "category" in item,
            "category": item.get("category", "(default)"),
            "operation_set": "operation" in item and item["operation"] is not None,
            "effect_defined": effect is not None,
            "source_filled": effect is not None and bool(effect.get("source", {})),
            "vitals_filled": effect is not None and bool(effect.get("vitals", {})),
            "experience_filled": effect is not None and bool(effect.get("experience", {})),
            "test_referenced": idx in test_refs,
        }
        rows.append(row)
    return rows


def render_report(rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append(f"指令覆盖矩阵 ({len(rows)} 条)")
    lines.append("-" * 80)
    lines.append(
        f"{'idx':>4} {'label':<12} {'cat':<4} {'op':<3} {'effect':<6} {'src':<4} {'vit':<4} {'exp':<4} {'test':<4}"
    )
    lines.append("-" * 80)

    missing_category: list[int] = []
    missing_effect: list[int] = []
    missing_source: list[int] = []

    for r in rows:
        cat_flag = "Y" if r["category_set"] else "N"
        op_flag = "Y" if r["operation_set"] else "."
        eff_flag = "Y" if r["effect_defined"] else "N"
        src_flag = "Y" if r["source_filled"] else "N"
        vit_flag = "Y" if r["vitals_filled"] else "."
        exp_flag = "Y" if r["experience_filled"] else "."
        test_flag = "Y" if r["test_referenced"] else "."
        lines.append(
            f"{r['index']:>4} {r['label']:<12} {cat_flag:<4} {op_flag:<3} {eff_flag:<6} {src_flag:<4} {vit_flag:<4} {exp_flag:<4} {test_flag:<4}"
        )

        if not r["category_set"]:
            missing_category.append(r["index"])
        if not r["effect_defined"]:
            missing_effect.append(r["index"])
        elif not r["source_filled"]:
            missing_source.append(r["index"])

    lines.append("-" * 80)
    lines.append(f"未显式设置 category: {len(missing_category)} 条")
    lines.append(f"未定义 effect:        {len(missing_effect)} 条")
    lines.append(f"effect 无 source:     {len(missing_source)} 条")
    lines.append("")
    lines.append("图例: cat=category, op=operation, effect=效果块存在, src=source已填, vit=vitals已填, exp=experience已填, test=测试引用")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Command coverage matrix")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()
    root = Path(args.root)
    rows = build_matrix(root)
    print(render_report(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
