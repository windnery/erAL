from __future__ import annotations

from random import randint, random, choices
from typing import TYPE_CHECKING
from config.mood_config import (
    MOOD_GOOD, MOOD_NEUTRAL, MOOD_BAD,
    MOOD_GOOD_RATE, MOOD_NEUTRAL_RATE, MOOD_BAD_RATE,
    MOOD_HALF_SATURATION, MOOD_MAX_PROB, MOOD_DECAY_INTERVAL
)
from config.source_config import POSITIVE_SRC, NEGATIVE_SRC

if TYPE_CHECKING:
    from game_engine.models.shipgirl import ShipGirl


def mood_proc(source: dict[str, int], npc: ShipGirl) -> None:
    """source到心情的计算"""
    pos = sum(v for k, v in source.items() if k in POSITIVE_SRC)
    neg = sum(v for k, v in source.items() if k in NEGATIVE_SRC)
    net = pos - neg
    if net == 0:
        return
    p = min(100 * abs(net) // (abs(net) + MOOD_HALF_SATURATION), MOOD_MAX_PROB)
    if npc.has_talent('emotional_deficiency'):
        p //= 2
    if randint(0, 99) < p:
        npc.set_mood(npc.get_mood() + (1 if net > 0 else -1))


def mood_natural_change(npc: ShipGirl, dt: int) -> None:
    """心情随时间向平静(0)自然靠近"""
    if dt <= 0:
        return
    mood = npc.get_mood()
    if mood == MOOD_NEUTRAL:
        return
    # 计算衰减概率
    prob = min(dt / MOOD_DECAY_INTERVAL, 1.0)
    if random() < prob:
        if mood > MOOD_NEUTRAL:
            npc.set_mood(mood - 1)
        elif mood < MOOD_NEUTRAL:
            npc.set_mood(mood + 1)


def roll_daily_mood() -> int:
    """按设定好的概率随机生成新一天的心情"""
    return choices(
        [MOOD_GOOD, MOOD_NEUTRAL, MOOD_BAD],
        weights=[MOOD_GOOD_RATE, MOOD_NEUTRAL_RATE, MOOD_BAD_RATE]
    )[0]
