from config.attr_defs import ATTR_DEFS
from game_engine.models.character import Character


def exp_calc(exp: str, chara: Character, num: int = 1):
    """计算exp获得"""
    mes: str = ""
    chara.exp[exp] += num
    mes = f"{ATTR_DEFS['exp'][exp]['name']}+{num} ({chara.name})"

    return mes
