from random import randint

from game_engine.managers import register_activity
from game_engine.models.activity import Activity
from game_engine.models.shipgirl import ShipGirl


@register_activity("relax")
class Relax(Activity):
    """放松活动类"""

    def __init__(self, sg: ShipGirl, id: str = "relax", start_time = None):
        super().__init__(sg=sg, id=id, start_time=start_time)
        self.duration = randint(40, 60)  # 放松活动持续时间(分钟)
        self.weight = 1
        self.on_start()  # 调用 on_start 方法初始化活动开始逻辑

    def on_start(self):
        """放松活动开始时的处理逻辑"""
        mes = f"{self.sg.name} 开始放松了"

        return mes

    def on_end(self):
        """放松活动结束时的处理逻辑"""
        mes = f"{self.sg.name} 结束了放松"
        return mes

    def tick(self, minutes: int):
        """放松活动进行中的处理逻辑"""
        # 每分钟恢复0.5%体力和气力
        stamina_recovery = int(self.sg.get_max_stamina() * 0.005 * minutes)
        energy_recovery = int(self.sg.get_max_energy() * 0.005 * minutes)
        self.sg.set_stamina(self.sg.get_stamina() + stamina_recovery)
        self.sg.set_energy(self.sg.get_energy() + energy_recovery)
        # 更新活动持续时间
        self.duration = max(self.duration - minutes, 0)
        
        mes = f"{self.sg.name} 正在放松 体力+{stamina_recovery} 气力+{energy_recovery}"
        return mes

    def get_weight(self):
        """获取活动权重"""
        # 体力和气力低于50%权重增加
        stamina_ratio = self.sg.get_stamina() / self.sg.get_max_stamina()
        energy_ratio = self.sg.get_energy() / self.sg.get_max_energy()
        if stamina_ratio < 0.5 or energy_ratio < 0.5:
            return self.weight + 2
        elif stamina_ratio < 0.3 or energy_ratio < 0.3:
            return self.weight + 3
        return self.weight

    def get_description(self):
        """获取活动描述"""
        return f"{self.sg.name} 正在放松"
        