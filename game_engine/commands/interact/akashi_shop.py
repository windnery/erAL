from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定：明石正在工作"""
    if npc.id == 'akashi' and npc.is_working():
        return True
    return False


@register_cmd('akashi_shop', '明石商店', '日常', can=can, frontend=True)
def akashi_shop(world: World, option: str):
    """明石商店（纯前端指令，后端不执行逻辑）

    点击指令后前端直接打开皮肤商店界面（skin_shop.js），
    商品展示/购买走后端 SkinManager 接口（get_shop_skins / buy_skin）。
    此函数仅作注册占位，返回空列表（无叙事文本）。
    """
    return []
