from config.abl_lv import ABL_LV
from config.source_kind import ALL_SOURCE_KEYS
from game_engine.models.character import Character


# def abl_lv_process(chara: Character, attr_defs: dict[str, dict[str, int]]):
#     '''检查角色的abl是否达到升级条件，若达到则升级'''
#     for exp_k, exp_v in chara.exp.items():
#         if exp_v >= 1000:
#             continue  # 经验值达到上限，不再升级
#         abl_k = exp_k.replace('exp', 'abl')
#         if exp_v >= ABL_LV[chara.abl[abl_k] + 1]:
#             chara.abl[abl_k] += 1
#             return f'{chara.name}的{attr_defs[abl_k]["name"]}变成了{chara.abl[abl_k]}！'
#     return None

def new_source(base: dict[str, int]):
    '''根据base生成新的source'''
    s = {k: 0 for k in ALL_SOURCE_KEYS}
    if base: s.update(base)
    return s

def low_intimacy2favor(intimacy_abl: int) -> int:
    '''亲密低会导致好感度下降'''
    if intimacy_abl == 0:
        return -3
    elif intimacy_abl == 1:
        return -2
    elif intimacy_abl == 2:
        return -1
    else:
        return 0

def low_favor2favor(favor: int) -> int:
    '''好感度低会导致好感度下降'''
    if favor <= 50:
        return -3
    elif favor <= 100:
        return -2
    elif favor <= 250:
        return -1
    else:
        return 0
