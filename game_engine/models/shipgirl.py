from dataclasses import dataclass, field
from typing import Any

from config.base_config import MAX_RATIONALITY, MIN_EMOTION, MAX_EMOTION
from game_engine.models.character import Character


@dataclass
class ShipGirl(Character):
    """舰娘类"""

    favor: int = 0  # 好感度
    trust: int = 0  # 信赖度
    talk_fatigue: int = 0  # 会话疲劳值
    is_talk_fatigue: bool = False  # 是否会话疲劳
    schedule: dict[str, Any] = field(default_factory=dict)  # 作息时间表
    color: str = '#ffffff'

    def get_state(self):
        """返回舰娘状态"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "favor": self.favor,
            "trust": self.trust,
            "base": self.base,
            "abl": self.abl,
            "cflag": self.cflag,
            "exp": self.exp,
            "palam": self.palam,
            "palam_lv": self.palam_lv,
            "talent": self.get_talent_list(),
            "schedule": self.schedule,
        }

    def get_emotion(self):
        """获取情绪值"""
        return self.base.get("emotion", MIN_EMOTION)

    def set_emotion(self, value: int):
        """设置情绪值"""
        self.base['emotion'] = min(max(value, 0), MAX_EMOTION)

    def emotion_natural_change(self, dt: int):
        """情绪自然变化"""
        emotion = self.get_emotion()
        self.set_emotion(emotion - dt * 4 * (emotion + 500) // 500)

    def reset_emotion(self):
        """重置情绪值"""
        self.set_emotion(MIN_EMOTION)

    def get_rationality(self):
        """获取理性值"""
        return self.base.get("rationality", MAX_RATIONALITY)

    def set_rationality(self, value: int):
        """设置理性值"""
        self.base['rationality'] = min(max(value, 0), MAX_RATIONALITY)

    def rationality_natural_change(self, dt: int):
        """理性自然变化"""
        rationality = self.get_rationality()
        self.set_rationality(rationality + dt * (MAX_RATIONALITY + 500) // (rationality + 500))

    def reset_rationality(self):
        """重置理性值"""
        self.set_rationality(MAX_RATIONALITY)

    def is_sleeping(self) -> bool:
        """是否正在睡觉"""
        return self.cflag.get("sleeping", False)

    def is_working(self) -> bool:
        """是否正在工作"""
        return self.cflag.get("working", False)

    def is_following(self) -> bool:
        """是否正在跟随"""
        is_following = (
            self.cflag.get("following", False)
            or self.cflag.get("secretary_ship_following", False)
            or self.cflag.get("dating_following", False)
        )
        return is_following

    def is_dating(self) -> bool:
        """是否正在约会"""
        return self.cflag.get("dating", False)

    def talk_fatigue_decay(self, dt: int):
        """会话疲劳值衰减"""
        self.talk_fatigue = max(self.talk_fatigue - dt, 0)
