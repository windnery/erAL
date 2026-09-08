from typing import ClassVar

from game_engine.models.shipgirl import ShipGirl


class Activity:
    """活动类"""
    loc_tags: ClassVar[list[str]] = []  # 活动地点标签列表
    weight = 0  # 活动权重(用于活动优先级排序)

    def __init__(self, id: str = "", start_time: int | None = None):
        self.id = id  # 活动ID
        self.start_time = start_time  # 活动开始时间(绝对分钟)
        self.duration = None  # 活动持续时间(分钟)

    def on_start(self, sg: ShipGirl) -> str:
        """活动开始时的处理逻辑"""
        return ""

    def on_end(self, sg: ShipGirl) -> str:
        """活动结束时的处理逻辑"""
        return ""

    def tick(self, sg: ShipGirl, minutes: int) -> str:
        """活动进行中的处理逻辑"""
        return ""

    @classmethod
    def get_weight(cls, sg: ShipGirl) -> int:
        """获取活动权重"""
        return cls.weight

    def get_description(self, sg: ShipGirl) -> str:
        """获取活动描述"""
        return ""
