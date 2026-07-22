
class TimeManager:
    def __init__(self, player):
        self.day = 1
        self.hour = 7
        self.minute = 0
        self.player = player

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
        stamina_recovery_time = (self.player.max_stamina - self.player.stamina) * 600 // self.player.max_stamina
        energy_recovery_time = (self.player.max_energy - self.player.energy) * 600 // self.player.max_energy
        return max(stamina_recovery_time, energy_recovery_time)

    def to_next_day(self):
        # 推进到正常睡觉的醒来时间
        minutes_to_advance = self.get_sleep_time()
        self.advance_time(minutes_to_advance)

