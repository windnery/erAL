from typing import TYPE_CHECKING

from game_engine.commands._commands import register_cmd
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定：不知火正在工作"""
    if npc.id == 'shiranui' and npc.is_working():
        return True
    return False


@register_cmd('shiranui_shop', '不知火商店', '日常', can, frontend=True)
def shiranui_shop(world: World, option: str):
    """不知火商店（纯前端指令，后端不执行逻辑）"""
    return []