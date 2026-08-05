from dataclasses import dataclass, field
import random
from typing import Any

from config.mood_enum import Mood
from game_engine.models.character import Character


@dataclass
class ShipGirl(Character):
    '''舰娘类'''
    favor: int = 0  # 好感度
    trust: int = 0  # 信赖度
    schedule: dict[str, Any] = field(default_factory=dict)   # 作息时间表
    lines: list[dict[str, Any]] = field(default_factory=list)  # 台词

    def get_state(self):
        '''返回舰娘状态'''
        return {
            'id': self.id,
            'name': self.name,
            'favor': self.favor,
            'trust': self.trust,
            'base': self.base,
            'abl': self.abl,
            'cflag': self.cflag,
            'exp': self.exp,
            'palam': self.palam,
            'palam_lv': self.palam_lv,
            'talent': self.get_talent_list(),
            'schedule': self.schedule,
            'mood_label': self.get_mood().value,
        }

    def get_line(self, action: str) -> str | None:
        '''获取台词'''
        candidates = [l for l in self.lines if l['action'] == action
                      and self._check_conditions(l.get('conditions', {}))]
        if not candidates:
            return None
        # 随机选择一条台词
        line = random.choice(candidates)
        texts = line.get('texts', [])
        if not texts:
            return None
        return random.choice(texts)

    def _check_conditions(self, conds: dict[str, Any]) -> bool:
        '''检查条件是否满足'''
        for key, value in conds.items():
            if key == 'min_favor' and self.favor < value:
                return False
            elif key == 'max_favor' and self.favor > value:
                return False
            elif key == 'min_trust' and self.trust < value:
                return False
            elif key == 'max_trust' and self.trust > value:
                return False
            # TODO: 后续条件检查在这里添加
        return True

    def get_mood(self) -> Mood:
        '''获取心情值'''
        if -10 <= self.base.get('mood', 0) < -5:
            return Mood.ANGRY
        elif -5 <= self.base.get('mood', 0) < 0:
            return Mood.UNHAPPY
        elif 0 <= self.base.get('mood', 0) < 2:
            return Mood.NEUTRAL
        elif 2 <= self.base.get('mood', 0) < 5:
            return Mood.HAPPY
        elif 5 <= self.base.get('mood', 0) < 8:
            return Mood.DELIGHTED
        else:
            return Mood.BLISS
