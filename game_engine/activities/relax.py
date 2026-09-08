from random import randint
from typing import ClassVar

from game_engine.managers import register_activity
from game_engine.models.activity import Activity
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import c_recover


@register_activity("relax")
class Relax(Activity):
    """放松活动类"""
    loc_tags: ClassVar[list[str]] = ["CAN_SIT_LOC"]  # 可进行放松活动的地点标签
    weight = 1

    def __init__(self, id: str = "relax", start_time = None):
        super().__init__(id=id, start_time=start_time)
        self.duration = randint(40, 60)  # 放松活动持续时间(分钟)

    def on_start(self, sg: ShipGirl):
        """放松活动开始时的处理逻辑"""
        mes = f"{sg.name} 开始放松了"

        return mes

    def on_end(self, sg: ShipGirl):
        """放松活动结束时的处理逻辑"""
        mes = f"{sg.name} 结束了放松"
        return mes

    def tick(self, sg: ShipGirl, minutes: int):
        """放松活动进行中的处理逻辑"""
        # 每分钟恢复0.5%体力和气力
        stamina_recovery = int(sg.get_max_stamina() * 0.005 * minutes)
        energy_recovery = int(sg.get_max_energy() * 0.005 * minutes)
        sg.set_stamina(sg.get_stamina() + stamina_recovery)
        sg.set_energy(sg.get_energy() + energy_recovery)
        # 更新活动持续时间
        self.duration = max(self.duration - minutes, 0)
        
        mes = f"{sg.name} 正在放松 " + c_recover(f"体力+{stamina_recovery} 气力+{energy_recovery}")
        return mes

    @classmethod
    def get_weight(cls, sg: ShipGirl):
        """获取活动权重"""
        # 体力和气力低于50%权重增加
        stamina_ratio = sg.get_stamina() / sg.get_max_stamina()
        energy_ratio = sg.get_energy() / sg.get_max_energy()
        if stamina_ratio < 0.3 or energy_ratio < 0.3:
            return cls.weight + 3
        elif stamina_ratio < 0.5 or energy_ratio < 0.5:
            return cls.weight + 2
        return cls.weight

    def get_description(self, sg: ShipGirl):
        """获取活动描述"""
        return f"{sg.name} 正在放松"
        