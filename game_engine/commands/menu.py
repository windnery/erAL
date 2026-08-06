from __future__ import annotations
from typing import TYPE_CHECKING
from game_engine.commands._commands import register_cmd

if TYPE_CHECKING:
    from world import World


@register_cmd('open_your_eyes', '睁开眼睛', '菜单', needs_target=False)
def open_your_eyes(world: World, option=None):
    """睁开眼睛：结束缓冲菜单，进入游戏"""
    world.menu_active = False
    return []


@register_cmd('set_wake_up_time', '设定起床时间', '菜单', needs_target=False)
def set_wake_up_time(world: World, option=None):
    """设定起床时间：option 为 {hour, minute}"""
    if not option or 'hour' not in option or 'minute' not in option:
        return ['输入无效']
    hour = int(option['hour'])
    minute = int(option.get('minute', 0))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        return ['输入无效']
    world.player.wake_time = {'hour': hour, 'minute': minute}
    return []


@register_cmd('set_secretary_ship', '设定秘书舰', '菜单', needs_target=False)
def set_secretary_ship(world: World, option=None):
    """设定秘书舰：option 为 {shipgirl_id}"""
    sg_id = option['shipgirl_id']
    npc_manager = world.npc_manager
    # 设定秘书舰后的处理
    npc_manager.set_secretary_ship_proc(sg_id, world.player)

    return []
