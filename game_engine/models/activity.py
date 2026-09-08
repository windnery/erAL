from game_engine.models.shipgirl import ShipGirl


class Activity:
    """活动类"""

    def __init__(self, sg: ShipGirl, id: str = "", start_time: int | None = None):
        self.sg = sg  # 挂上该活动的舰娘
        self.id = id  # 活动ID
        self.start_time = start_time  # 活动开始时间(绝对分钟)
        self.duration = None  # 活动持续时间(分钟)
        self.weight = 0  # 活动权重(用于活动优先级排序)

    def on_start(self) -> str:
        """活动开始时的处理逻辑"""
        return ""

    def on_end(self) -> str:
        """活动结束时的处理逻辑"""
        return ""

    def tick(self, minutes: int) -> str:
        """活动进行中的处理逻辑"""
        return ""

    def get_weight(self):
        """获取活动权重"""
        return self.weight

    def get_description(self) -> str:
        """获取活动描述"""
        return ""
