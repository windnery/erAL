from game_engine.commands._commands import register_cmd


@register_cmd('open_your_eyes', '睁开眼睛', '菜单', needs_target=False)
def open_your_eyes(world, option=None):
    """睁开眼睛：结束缓冲菜单，进入游戏"""
    world.menu_active = False
    return []


@register_cmd('set_wake_up_time', '设定起床时间', '菜单', needs_target=False)
def set_wake_up_time(world, option=None):
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
def set_secretary_ship(world, option=None):
    """设定秘书舰：option 为 {shipgirl_id}"""
    if not option or 'shipgirl_id' not in option:
        return ['输入无效']
    sg_id = option['shipgirl_id']
    npc_manager = world.npc_manager
    if sg_id not in npc_manager.shipgirls:
        return ['没有这个舰娘']
    npc_manager.secretary_ship = npc_manager.shipgirls[sg_id]
    return []
