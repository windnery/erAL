"""口上（对白）模块：每个角色一个文件，每个 action 一个函数。

函数签名：``def <action>(c: ShipGirl) -> list[list[str]] | None``
- 返回候选场景列表，每个场景 = 消息列表（台词带「」，地文裸文本，``{name}`` 为名字占位）
- 无口上返回 ``None``（渲染层静默）
- 优先级 = 函数内 ``if/elif`` 书写顺序；随机选择由 ``get_scene`` 完成，保证可测
"""

from __future__ import annotations

import random
from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

# chara_id -> 口上模块名（本包内）
_CHARA_MODULES: dict[str, str] = {
    "laffey": "laffey",
    "javelin": "javelin",
    "Z23": "Z23",
    "ayanami": "ayanami",
}

_MODULE_CACHE: dict[str, Any] = {}


def _get_module(chara_id: str):
    module_name = _CHARA_MODULES.get(chara_id)
    if module_name is None:
        return None
    if module_name not in _MODULE_CACHE:
        _MODULE_CACHE[module_name] = import_module(f".{module_name}", __name__)
    return _MODULE_CACHE[module_name]


import inspect


def get_scene(chara, action: str, player_name: str = "") -> list[str] | None:
    """获取角色某个 action 的口上场景（消息列表）；无口上返回 None。"""
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
