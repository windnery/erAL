from random import randint

from game_engine.managers import register_activity
from game_engine.models.activity import Activity
from game_engine.models.shipgirl import ShipGirl


@register_activity("free")
class Free(Activity):
    """自由活动类"""

    def __init__(self, sg: ShipGirl, id: str = "free", start_time = None):
        super().__init__(sg=sg, id=id, start_time=start_time)
        self.duration = randint(20, 30)  # 自由活动持续时间(分钟)
        self.weight = 3
        # 因为自由活动没有特殊的开始逻辑，所以不额外调用 on_start 方法产生不必要的开销

    def on_start(self):
        """自由活动开始时的处理逻辑"""
        # 自由活动没有特殊的开始逻辑
        return ""

    def on_end(self):
        """自由活动结束时的处理逻辑"""
        # 自由活动没有特殊的结束逻辑
        return ""

    def tick(self, minutes: int):
        """自由活动进行中的处理逻辑"""
        # 自由活动没有特殊的进行逻辑
        return ""

    def get_weight(self):
        """获取活动权重"""
        return self.weight
        