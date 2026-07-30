from config.abl_lv import abl_lv
from config.source_kind import ALL_SOURCE_KEYS
from game_engine.models.character import Character


def abl_lv_process(chara: Character, attr_defs: dict[str, dict[str, int]]):
    '''检查角色的abl是否达到升级条件，若达到则升级'''
    for exp_k, exp_v in chara.exp.items():
        if exp_v >= 1000:
            continue  # 经验值达到上限，不再升级
        abl_k = exp_k.replace('exp', 'abl')
        if exp_v >= abl_lv[chara.abl[abl_k] + 1]:
            chara.abl[abl_k] += 1
            return f'{chara.name}的{attr_defs[abl_k]["name"]}变成了{chara.abl[abl_k]}！'
    return None

def new_source(base: dict[str, int]):
    '''根据base生成新的source'''
    s = {k: 0 for k in ALL_SOURCE_KEYS}
    if base: s.update(base)
    return s
