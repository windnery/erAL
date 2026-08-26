from __future__ import annotations

from config.initiative_config import (
    INITIATIVE_BASE_GROWTH,
    INITIATIVE_S_MAX,
    ORGASM_INITIATIVE_RATE_LV,
    ORGASM_INITIATIVE_MULT_NUM,
)
from config.source_config import PLEASURE_SRC
from game_engine.models.character import Character


def pleasure_sum(source: dict) -> int:
    """该份source中的快感系source之和"""
    return int(sum(source.get(k, 0) or 0 for k in PLEASURE_SRC))


def growth_delta(received: int) -> int:
    """按受到的快感source之和计算本轮主导权增长值（下限0）"""
    suppress = max(0.0, 1.0 - received / INITIATIVE_S_MAX)
    return int(INITIATIVE_BASE_GROWTH * suppress)


def initiative_grow_proc(train, chara_pleasures: list[tuple[Character, int]]) -> list[str]:
    """每轮主导权增长结算：所有参与者基础增长，受快感越多增长越少

    chara_pleasures: [(角色, 本轮受到的快感系source之和), ...]
    """
    mes: list[str] = []
    for chara, received in chara_pleasures:
        if chara.id not in train.initiative:
            continue
        # 神志不清：主导权不再增长
        if chara.cflag.get('unconscious'):
            continue
        delta = growth_delta(received)
        if delta <= 0:
            continue
        train.initiative[chara.id] += delta
        mes.append(f'主导权+{delta}（{chara.name}）')
    return mes


def initiative_orgasm_proc(train, target: Character, max_lv: int, orgasm_num: int) -> str:
    """舰娘绝顶主导权衰减：衰减率 = 等级系数 × 部位数乘数"""
    if max_lv < 1 or target.id not in train.initiative:
        return ''
    rate = ORGASM_INITIATIVE_RATE_LV.get(max_lv, 0.0)
    mult = ORGASM_INITIATIVE_MULT_NUM.get(orgasm_num, 1.0)
    loss = int(train.initiative[target.id] * rate * mult)
    if loss <= 0:
        return ''
    train.initiative[target.id] = max(0, train.initiative[target.id] - loss)
    return f'[[c:#ffd400]]{target.name}被玩弄到顶峰！主导权-{loss}[[/c]]'


def initiative_ejaculation_proc(train, player: Character) -> str:
    """玩家射精主导权整除2"""
    pid = player.id
    if pid not in train.initiative:
        return ''
    old = train.initiative[pid]
    new = old // 2
    train.initiative[pid] = new
    if new == old:
        return ''
    return f'[[c:#ffd400]]{player.name}射精失神，主导权 {old} → {new}！[[/c]]'
