from game_engine.managers import register_activity
from game_engine.models.activity import Activity
from game_engine.models.shipgirl import ShipGirl


@register_activity("free")
class Free(Activity):
    """自由活动类"""
    weight = 3

    def __init__(self, id: str = "free", start_time = None):
        super().__init__(id=id, start_time=start_time)
        self.duration = 0  # 自由活动持续时间无意义 直接在update_position中处理自由活动的逻辑
        # 因为自由活动没有特殊的开始逻辑，所以不额外调用 on_start 方法产生不必要的开销

    def on_start(self, sg: ShipGirl):
        """自由活动开始时的处理逻辑"""
        # 自由活动没有特殊的开始逻辑
        return ""

    def on_end(self, sg: ShipGirl):
        """自由活动结束时的处理逻辑"""
        # 自由活动没有特殊的结束逻辑
        return ""

    def tick(self, sg: ShipGirl, minutes: int):
        """自由活动进行中的处理逻辑"""
        # 自由活动没有特殊的进行逻辑
        return ""

    @classmethod
    def get_weight(cls, sg: ShipGirl):
        """获取活动权重"""
        return cls.weight
        