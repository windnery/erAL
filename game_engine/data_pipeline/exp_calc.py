from config.attr_defs import ATTR_DEFS
from game_engine.models.character import Character


def exp_calc(exp: str, chara: Character, num: int = 1):
    """计算exp获得"""
    chara.set_exp(exp, num + chara.get_exp(exp))
    mes = f"{ATTR_DEFS['exp'][exp]['name']}+{num} ({chara.name})"

    if chara.has_talent('no_kiss_exp') and chara.exp['kiss_exp'] > 0:
        chara.talent.pop('no_kiss_exp')

    return mes
