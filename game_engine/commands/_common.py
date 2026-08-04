from config.abl_lv import ABL_LV
from config.source_kind import ALL_SOURCE_KEYS
from game_engine.models.character import Character


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
