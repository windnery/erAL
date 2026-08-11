# 修正系数
from config.palam_config import PALAM2SRC_WEIGHTS

K_ACCEL = 0.3


def palam2src(palam_lv: dict[str, int], source: dict[str, int | float]) -> dict[str, int]:
    """palam_lv对source的修正"""
    for palam_key, lv in palam_lv.items():
        if lv <= 0:
            continue
        modify = lv * (1 + K_ACCEL * (lv - 1) / 2)
        # 每个 palam 按权重表修正对应 source
        for src_key, coef in PALAM2SRC_WEIGHTS.get(palam_key, {}).items():
            if not source.get(src_key, 0):
                continue
            source[src_key] += int(coef * modify)
            # 避免 source 值小于 0
            source[src_key] = max(source[src_key], 0)
