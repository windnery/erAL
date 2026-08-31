from dataclasses import dataclass, field
from typing import Any, ClassVar

from config.base_config import MAX_RATIONALITY, MIN_EMOTION, MAX_EMOTION
from config.mood_config import MOOD_LABELS, MOOD_COLORS, MOOD_BAD, MOOD_BLISS
from game_engine.models.character import Character


@dataclass
class ShipGirl(Character):
    """舰娘类"""

    favor: int = 0  # 好感度
    trust: int = 0  # 信赖度
    mark: dict[str, int] = field(default_factory=dict)  # 刻印
    talk_fatigue: int = 0  # 会话疲劳值
    is_talk_fatigue: bool = False  # 是否会话疲劳
    schedule: dict[str, Any] = field(default_factory=dict)  # 作息时间表
    color: str = '#ffffff'
    DEFAULT_BODY_SLOTS: ClassVar[dict[str, int]] = {
        'hands': 2,
        'mouth': 1,
        'breasts': 2,
        'clitoris': 1,
        'vagina': 1,
        'ass': 1,
        'feet': 2
    }

    def __post_init__(self):
        from copy import deepcopy
        super().__post_init__()
        # 身体槽位
        self.body_slots = deepcopy(self.DEFAULT_BODY_SLOTS)

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
            "mood": self.get_mood(),
            "mood_label": self.get_mood_label(),
            "mood_color": self.get_mood_color(),
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

    def get_mood(self) -> int:
        """获取心情值"""
        return self.base.get("mood", 0)

    def set_mood(self, value: int):
        """设置心情值"""
        value = min(max(value, MOOD_BAD), MOOD_BLISS)
        self.base['mood'] = value

    def get_mood_label(self) -> str:
        """获取心情标签"""
        return MOOD_LABELS[self.get_mood()]

    def get_mood_color(self) -> str:
        """获取心情颜色"""
        return MOOD_COLORS.get(self.get_mood(), '')

    def apply_mood_change(self, value: int):
        """应用心情变化"""
        self.set_mood(self.get_mood() + value)

    def mood_natural_change(self, dt: int):
        """心情自然变化"""
        from game_engine.data_pipeline.mood.mood_calc import mood_natural_change
        mood_natural_change(self, dt)

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

    def talk_fatigue_decay(self, dt: int):
        """会话疲劳值衰减"""
        self.talk_fatigue = max(self.talk_fatigue - dt, 0)
