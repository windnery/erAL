"""json 口上数据加载与 ``when`` 条件求值。

数据目录：``data/dialogue/<chara_id>.json``。
格式与 ``when`` 词汇表见 ``config/dialogue_config.py`` 模块 docstring。

选择语义：按条目顺序取**第一个** ``when`` 命中的条目，再在其中 ``variants`` 内
随机选一个场景——与 Python 口上的 ``if/elif`` + ``random.choice`` 完全一致。
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dialogue"

# when 词汇表（与 config/dialogue_config.py docstring 保持一致）
KNOWN_WHEN_KEYS: frozenset[str] = frozenset({
    "relationship", "lover", "dating", "flags", "talents",
    "talent_values", "marks", "mood", "outcome", "favor", "trust",
})

_DIALOGUE_CACHE: dict[str, dict[str, Any] | None] = {}


def load_dialogue(chara_id: str) -> dict[str, Any] | None:
    """加载并缓存角色 json 口上；文件不存在返回 ``None``。"""
    if chara_id in _DIALOGUE_CACHE:
        return _DIALOGUE_CACHE[chara_id]
    path = DATA_DIR / f"{chara_id}.json"
    data: dict[str, Any] | None = None
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    _DIALOGUE_CACHE[chara_id] = data
    return data


def list_chara_ids() -> set[str]:
    """数据目录中已存在 json 口上的角色 id 集合。"""
    if not DATA_DIR.exists():
        return set()
    return {p.stem for p in DATA_DIR.glob("*.json")}


def _match_range(value: int, spec: Any) -> bool:
    """``int | [int, ...] | {"min": int, "max": int}`` 的区间/枚举匹配。"""
    if isinstance(spec, dict):
        lo = spec.get("min")
        hi = spec.get("max")
        if lo is not None and value < lo:
            return False
        if hi is not None and value > hi:
            return False
        return True
    if isinstance(spec, (list, tuple)):
        return value in spec
    return value == spec


def _match_keys(present: set[str], spec: dict[str, list[str]]) -> bool:
    """``flags`` / ``talents`` 的 ``{any, all, not}`` 存在性判定。"""
    any_keys = spec.get("any", [])
    all_keys = spec.get("all", [])
    not_keys = spec.get("not", [])
    if any_keys and not any(k in present for k in any_keys):
        return False
    if all_keys and not all(k in present for k in all_keys):
        return False
    if any(k in present for k in not_keys):
        return False
    return True


def match_when(chara, when: dict[str, Any], outcome: str | None = None) -> bool:
    """判定 ``when`` 条件是否命中角色当前状态。

    同一 ``when`` 内多键为**与**；未知键视为不命中（避免静默匹配全部）。
    """
    for key, spec in when.items():
        if key == "relationship":
            if not _match_range(chara.get_talent_value("relationship"), spec):
                return False
        elif key == "lover":
            if chara.has_talent("lover") != bool(spec):
                return False
        elif key == "dating":
            if chara.is_dating() != bool(spec):
                return False
        elif key == "flags":
            present = {k for k, v in chara.cflag.items() if v}
            if not _match_keys(present, spec):
                return False
        elif key == "talents":
            if not _match_keys(set(chara.talent.keys()), spec):
                return False
        elif key == "talent_values":
            for tkey, tspec in spec.items():
                if not _match_range(chara.get_talent_value(tkey), tspec):
                    return False
        elif key == "marks":
            for mkey, mspec in spec.items():
                if not _match_range(chara.mark.get(mkey, 0), mspec):
                    return False
        elif key == "mood":
            if not _match_range(chara.get_mood(), spec):
                return False
        elif key == "outcome":
            if outcome != spec:
                return False
        elif key in ("favor", "trust"):
            if not _match_range(getattr(chara, key), spec):
                return False
        else:
            return False
    return True


def _render(text: str, chara, player_name: str) -> str:
    """替换 ``{name}`` / ``{chara}`` 占位符。"""
    return text.replace("{name}", player_name).replace("{chara}", chara.name)


def get_json_scene(
    chara, action: str, player_name: str = "", outcome: str | None = None
) -> list[str] | None:
    """按 json 口上取场景；json 无该 action（或全部未命中）返回 ``None``。"""
    data = load_dialogue(chara.id)
    if data is None:
        return None
    entries = data.get("actions", {}).get(action)
    if not entries:
        return None
    for entry in entries:
        when = entry.get("when")
        if when and not match_when(chara, when, outcome):
            continue
        variants = entry.get("variants")
        if not variants:
            continue
        scene = random.choice(variants)
        if not isinstance(scene, list):
            scene = [scene]
        return [_render(msg, chara, player_name) for msg in scene]
    return None
