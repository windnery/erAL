from random import randint, choice

from game_engine.managers.MapManager import MapManager
from game_engine.managers.NpcManager import NpcManager
from game_engine.models.player import Player

class TimeManager:
    def __init__(self, player: Player, npc_manager: NpcManager, map_manager: MapManager):
        self.day = 1
        self.hour = 7
        self.minute = 0
        self.player = player
        self.npc_manager = npc_manager
        self.map_manager = map_manager

    def advance_time(self, minutes: int):
        # 推进时间
        self.minute += minutes
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1
        while self.hour >= 24:
            # 处理跨天
            self.hour -= 24
            self.day += 1

        # 每次推进时间后更新舰娘位置
        mes = []
        for sg in self.npc_manager.shipgirls.values():
            # 睡觉
            if self.hour >= sg.schedule['sleep'][0] or self.hour < sg.schedule['sleep'][1]:
                # 初始位置就是舰娘的家
                sleep_region = self.npc_manager.shipgirls_db[sg.id]['location']['region']
                sleep_node = self.npc_manager.shipgirls_db[sg.id]['location']['node']
                self.npc_manager.set_loc(sg.id, sleep_region, sleep_node)
                mes += [f"{sg.name}要回去睡觉了……"]
                continue
            # 工作
            work_time: list[list[int]] = sg.schedule['work']['time']
            is_work = False
            for time_range in work_time:
                if time_range[0] <= self.hour < time_range[1]:
                    work_region = sg.schedule['work']['location']['region']
                    work_node = sg.schedule['work']['location']['node']
                    self.npc_manager.set_loc(sg.id, work_region, work_node)
                    mes += [f"{sg.name}似乎有事匆匆离开了……"]
                    is_work = True
                    break
            # 自由行动
            if not is_work:
                # 每次推进时间舰娘会随机留在原地/去一个当前区域的节点/去一个别的区域
                # 留在原地:80%，去当前区域的节点:15%，去别的区域:5%
                p = randint(1, 100)
                if p <= 15:
                    # 去当前区域的节点
                    nodes = self.map_manager.get_available_nodes(sg.location['region'], sg.location['node'])
                    nodes = nodes[:-1]  # 移除返回选项
                    target_node = choice(nodes)
                    self.npc_manager.set_loc(sg.id, sg.location['region'], target_node['key'])
                    mes += [f"{sg.name}似乎去{target_node['name']}了……"]
                elif p <= 20:
                    # 去别的区域
                    regions = self.map_manager.get_available_regions(sg.location['region'])
                    regions = regions[:-1]  # 移除返回选项
                    target_region = choice(regions)
                    nodes = self.map_manager.get_available_nodes(target_region['key'], sg.location['node'])
                    target_node = choice(nodes)
                    self.npc_manager.set_loc(sg.id, target_region['key'], target_node['key'])
                    mes += [f"{sg.name}似乎去{target_region['name']}了……"]




    def get_period(self):
        # 获取当前时间段
        if 4 <= self.hour < 6:
            return {'key': 'dawn', 'name': '凌晨'}
        elif 6 <= self.hour < 11:
            return {'key': 'morning', 'name': '早晨'}
        elif 11 <= self.hour < 13:
            return {'key': 'noon', 'name': '中午'}
        elif 13 <= self.hour < 18:
            return {'key': 'afternoon', 'name': '下午'}
        elif 18 <= self.hour < 22:
            return {'key': 'evening', 'name': '夜晚'}
        else:
            return {'key': 'night', 'name': '深夜'}

    def get_state(self):
        # 获取当前时间状态
        return {
            'day': self.day,
            'hour': self.hour,
            'minute': self.minute,
            'period': self.get_period()
        }

    def get_sleep_time(self):
        # 获取正常睡觉的时间
        current = self.hour * 60 + self.minute
        target = 7 * 60  # 第二天早上7点
        if current > target:
            # 如果当前时间已经超过7点，则推进到第二天的7点
            minutes_to_advance = (24 * 60 - current) + target
        else:
            minutes_to_advance = target - current
        return minutes_to_advance

    def get_exhaustion_time(self):
        # 获取体力耗尽的休息时间
        # 体力耗尽后会一直睡到体力和气力恢复到最大值，假设每小时恢复体力和气力的1/10
        # 恢复速率: max/10 每小时 = max/600 每分钟，所需分钟数 = remaining * 600 / max
        stamina_recovery_time = (self.player.base['max_stamina'] - self.player.base['stamina']) * 600 // self.player.base['max_stamina']
        energy_recovery_time = (self.player.base['max_energy'] - self.player.base['energy']) * 600 // self.player.base['max_energy']
        return max(stamina_recovery_time, energy_recovery_time)

    def to_next_day(self):
        # 推进到正常睡觉的醒来时间
        minutes_to_advance = self.get_sleep_time()
        self.advance_time(minutes_to_advance)

