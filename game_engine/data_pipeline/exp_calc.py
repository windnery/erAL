from config.attr_defs import ATTR_DEFS
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl


def exp_calc(abl_list: list[str], player: Player, npc: ShipGirl|None = None, npc_gain: bool=False):
    """计算exp获得"""
    # TODO: 经验获得数值还需要调整
    mes: list[str] = []
    for abl in abl_list:
        player.exp[abl] += 1
        mes.append(f'{ATTR_DEFS['exp'][abl]['name']}+1 ({player.name})')
        if npc and npc_gain:
            npc.exp[abl] += 1
            mes.append(f'{ATTR_DEFS['exp'][abl]['name']}+1 ({npc.name})')

    return mes
