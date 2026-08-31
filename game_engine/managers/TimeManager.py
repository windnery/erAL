from game_engine.dialogue import get_scene
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

    def get_total_minutes(self) -> int:
        """获取从第1天0点开始的绝对游戏总分钟数"""
        return (self.day - 1) * 1440 + self.hour * 60 + self.minute

    def advance_time(self, minutes: int):
        # 推进时间（纯时间计算，不处理NPC逻辑）
        self.minute += minutes
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1
        while self.hour >= 24:
            # 处理跨天
            self.hour -= 24
            self.day += 1

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
        target = self.player.wake_time['hour'] * \
            60 + self.player.wake_time['minute']  # 醒来的时间
        if current >= target:
            # 如果当前时间已经超过设定的醒来时间，则推进到第二天
            minutes_to_advance = (24 * 60 - current) + target
        else:
            minutes_to_advance = target - current
        return minutes_to_advance

    def get_exhaustion_time(self):
        # 获取体力耗尽的休息时间
        # 体力耗尽后会一直睡到体力和气力恢复到最大值，假设每小时恢复体力和气力的1/10
        # 恢复速率: max/10 每小时 = max/600 每分钟，所需分钟数 = remaining * 600 / max
        stamina_recovery_time = (
            self.player.base['max_stamina'] - self.player.base['stamina']) * 600 // self.player.base['max_stamina']
        energy_recovery_time = (
            self.player.base['max_energy'] - self.player.base['energy']) * 600 // self.player.base['max_energy']
        return max(stamina_recovery_time, energy_recovery_time)

    def advance_time_with_events(self, minutes: int):
        """推进时间并返回玩家附近舰娘的变动消息
        返回: list[str] 事件消息列表"""
        r, n = self.player.location['region'], self.player.location['node']

        # 推进前：谁在这
        before = {sg.id: sg.name for sg in self.npc_manager.get_npcs_at(r, n)}

        # 推进时间
        self.advance_time(minutes)

        # 更新舰娘位置（当前时间由 NpcManager 内部读 time_manager，minutes 仅作推进量）
        self.npc_manager.update_positions(
            minutes, self.map_manager, self.player)

        # 推进后：谁在这
        after = {sg.id: sg.name for sg in self.npc_manager.get_npcs_at(r, n)}

        # 对比生成消息
        events = []
        for sg_id, name in before.items():
            if sg_id not in after:
                sg = self.npc_manager.get_npc_by_id(sg_id)
                events.append(
                    f'{name}前往了[[c:#ffd400]]{self.map_manager.get_region_name(sg.location["region"])}[[/c]]的[[c:#ffd400]]{self.map_manager.get_node_name(sg.location["region"], sg.location["node"])}[[/c]]')
        for sg_id, name in after.items():
            if sg_id not in before:
                events.append(f'{name}走了过来。')

        # encounter 事件
        for sg_id, name in after.items():
            if sg_id in before:
                continue  # 已经在这里的舰娘不触发 encounter
            sg = self.npc_manager.get_npc_by_id(sg_id)
            if not sg.is_following():
                # 未跟随
                events.append(f'遇到了[[c:{sg.color}]]{name}[[/c]]。')

            if not sg.cflag['have_encountered']:
                # 之前没见过
                sg.cflag['have_encountered'] = True
                events.append(f'第一次遇到{name}。')
                scene = get_scene(sg, 'first_encounter', self.player.name)
                if scene:
                    for msg in scene:
                        events.append(f'[[c:{sg.color}]]{msg}[[/c]]')

        return events

    def to_next_day(self):
        # 推进到正常睡觉的醒来时间
        minutes_to_advance = self.get_sleep_time()
        self.advance_time(minutes_to_advance)
