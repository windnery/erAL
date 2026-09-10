"""口上（对白）模块：三层混合架构。

1. json 数据层（首选）：``data/dialogue/<chara_id>.json``，条件与格式见
   ``config/dialogue_config.py``。
2. resolver 引擎：``_resolver.get_json_scene`` 求值 ``when`` 并选场景。
3. Python 逃生舱（回退）：本包内每个角色一个模块、每个 action 一个函数，
   用于 json 表达不了的复杂条件逻辑。

函数签名：``def <action>(c: ShipGirl) -> list[list[str]] | None``
- 返回候选场景列表，每个场景 = 消息列表。
- 无口上返回 ``None``（渲染层静默）。
- 优先级 = 函数内 ``if/elif`` 书写顺序；随机选择由 ``get_scene`` 完成，保证可测。
"""

from __future__ import annotations

import inspect
import random
from importlib import import_module
from typing import Any

from ._resolver import get_json_scene, list_chara_ids, load_dialogue

# chara_id -> 口上模块名（本包内，目前仅标枪保留）
_CHARA_MODULES: dict[str, str] = {
    "javelin": "javelin",
}

_MODULE_CACHE: dict[str, Any] = {}


def _get_module(chara_id: str):
    module_name = _CHARA_MODULES.get(chara_id)
    if module_name is None:
        return None
    if module_name not in _MODULE_CACHE:
        _MODULE_CACHE[module_name] = import_module(f".{module_name}", __name__)
    return _MODULE_CACHE[module_name]


def _get_py_scene(chara, action: str, player_name: str = "") -> list[str] | None:
    """Python 模块逃生舱：取 action 函数并随机选一个场景。"""
    module = _get_module(chara.id)
    if module is None:
        return None
    fn = getattr(module, action, None)
    if fn is None:
        return None
    try:
        sig = inspect.signature(fn)
        if len(sig.parameters) >= 2:
            scenes = fn(chara, player_name)
        else:
            scenes = fn(chara)
    except (TypeError, ValueError):
        try:
            scenes = fn(chara)
        except TypeError:
            scenes = fn(chara, player_name)
    if not scenes:
        return None
    return list(random.choice(scenes))


def get_scene(
    chara, action: str, player_name: str = "", outcome: str | None = None
) -> list[str] | None:
    """获取角色某个 action 的口上场景（消息列表）；无口上返回 None。

    先查 json 数据层，未命中再回退到 Python 模块（逃生舱）。
    ``outcome`` 供带成功率判定的指令使用（见 ``config/dialogue_config.py``）。
    """
    scene = get_json_scene(chara, action, player_name, outcome)
    if scene is not None:
        return scene
    return _get_py_scene(chara, action, player_name)


def known_chara_ids() -> set[str]:
    """已有口上来源（json 文件或 Python 模块）的角色 id 集合。"""
    return set(_CHARA_MODULES.keys()) | list_chara_ids()


def get_available_actions(chara_id: str) -> set[str]:
    """该角色已提供口上的 action key 集合（json ∪ Python 模块）。

    Python 模块按 ``ACTION_CONTRACT`` 过滤，排除 import 进来的无关名字。
    """
    from config.dialogue_config import ACTION_CONTRACT

    actions: set[str] = set()
    data = load_dialogue(chara_id)
    if data:
        actions.update(data.get("actions", {}).keys())
    module = _get_module(chara_id)
    if module is not None:
        actions.update(
            name for name in dir(module) if name in ACTION_CONTRACT
        )
    return actions
