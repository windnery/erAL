from game_engine.commands._commands import register_cmd


@register_cmd('show_chara_info', '查看角色信息', '日常', frontend=True)
def show_chara_info(world, option=None):
    """纯前端指令：面板渲染完全由前端 chara_info.js 完成，后端不做事。

    前端 commands.js 检测到 cmd.frontend 为真时，直接调用
    callbacks.showCharaInfo(选中舰娘id) 打开全屏角色信息面板，
    不会走到这里。返回空列表作为兜底（无叙事 → refresh）。
    """
    return []
