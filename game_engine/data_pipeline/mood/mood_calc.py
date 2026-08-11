from random import random

from config.source_config import POSITIVE_SRC, NEGATIVE_SRC
from game_engine.models.character import Character


def src2mood_proc(source: dict[str, int], npc: Character) -> int:
    '''source到mood的转换处理'''
    positive_src, negative_src = 0, 0
    for k, v in source.items():
        if k in POSITIVE_SRC:
            positive_src += v
        elif k in NEGATIVE_SRC:
            negative_src += v

    bonus = get_p_src2mood(positive_src)
    loss = get_n_src2mood(negative_src)

    return bonus - loss

def get_p_src2mood(src_value: int):
    '''正面source值到mood的转换'''
    res = 0
    if src_value < 1000:
        # 0.3概率+1
        if random() < 0.3:
            res += 1
    elif src_value < 1500:
        # 0.4概率+1
        if random() < 0.4:
            res += 1
    elif src_value < 2000:
        # 0.5概率+1
        if random() < 0.5:
            res += 1
    elif src_value < 2500:
        # 0.6概率+1
        if random() < 0.6:
            res += 1
    elif src_value < 3000:
        # 0.7概率+1
        if random() < 0.7:
            res += 1
    elif src_value < 4000:
        # 0.8概率+1
        if random() < 0.8:
            res += 1
    elif src_value < 5000:
        # 0.9概率+1
        if random() < 0.9:
            res += 1
    elif src_value < 6000:
        # 1.0概率+1
        res += 1
    elif src_value < 8000:
        # 1.0概率+2
        res += 2
    elif src_value < 10000:
        # 1.0概率+4
        res += 4
    elif src_value < 20000:
        # 1.0概率+6
        res += 6
    elif src_value < 30000:
        # 1.0概率+8
        res += 8
    else:
        # 1.0概率+10
        res += 10

    return res

def get_n_src2mood(src_value: int):
    '''负面source值到mood的转换 负面的影响更大'''
    res = 0
    if src_value < 500:
        # 0.3概率+1
        if random() < 0.3:
            res += 1
    elif src_value < 700:
        # 0.6概率+1
        if random() < 0.4:
            res += 1
    elif src_value < 1000:
        # 0.8概率+1
        if random() < 0.5:
            res += 1
    elif src_value < 1500:
        # 1.0概率+1
        res += 1
    elif src_value < 2000:
        # 1.0概率+2
        res += 2
    elif src_value < 3000:
        # 1.0概率+4
        res += 4
    elif src_value < 4000:
        # 1.0概率+6
        res += 6
    elif src_value < 6000:
        # 1.0概率+8
        res += 8
    else:
        # 1.0概率+10
        res += 10

    return res