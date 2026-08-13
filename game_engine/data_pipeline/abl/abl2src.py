# 修正系数
from config.abl_config import ABL2SRC_WEIGHTS

K_ACCEL = 0.5

def abl2src(abl: dict[str, int], source: dict[str, int]):
    """abl等级对source的修正"""
    for abl_key, lv in abl.items():
        if lv <= 0: continue
        modify = lv * (1 + K_ACCEL * (lv - 1) / 2)
        # 每个 abl 只修正自己语义对应的 source
        if abl_key not in ABL2SRC_WEIGHTS: continue
        for src_key, coef in ABL2SRC_WEIGHTS[abl_key].items():
            if source.get(src_key, 0):
                source[src_key] += int(coef * modify)
                # 避免 source 值小于 0
                source[src_key] = max(source[src_key], 0)

