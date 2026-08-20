from game_engine.commands._commands import register_cmd


@register_cmd('show_player_info', '查看个人信息', '系统', needs_target=False, frontend=True)
def show_player_info(world, option=None):
    """纯前端指令：玩家信息面板渲染完全由前端 player_info.js 完成。
    后端不做事，返回空列表作为兜底（无叙事 → refresh）。
    """
    return []
