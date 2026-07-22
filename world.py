from game_engine.managers.CommandManager import CommandManager
from game_engine.managers.MapManager import MapManager
from game_engine.managers.TimeManager import TimeManager
from game_engine.managers.WorkManager import WorkManager
from game_engine.models.player import Player


class World:
    def __init__(self):
        self.player = Player()
        self.map_manager = MapManager()
        self.time_manager = TimeManager(self.player)
        self.work_manager = WorkManager()
        self.command_manager = CommandManager(self)

    def get_state(self):
        '''一次性返回前端需要的全部状态'''
        return {
            'player': self.player.get_state(),
            'location': self.map_manager.get_current_loc(),
            'commands': self.command_manager.get_commands(),
            'time': self.time_manager.get_state()
        }

    def change_stamina(self, delta: int):
        '''包装一层改变体力的方法'''
        exhaustion = not self.player.set_stamina(self.player.stamina + delta)
        if exhaustion:
            return self.settle_day(exhaustion=True)
        return ''
    
    def change_energy(self, delta: int):
        '''包装一层改变气力的方法'''
        exhaustion = not self.player.set_energy(self.player.energy + delta)
        if exhaustion:
            # TODO: 后续做气力为0的影响
            pass
        return ''

    def settle_day(self, sleep: bool = False, exhaustion: bool = False):
        '''日终结算 
        sleep: 是否是睡觉结算
        exhaustion: 是否是体力耗尽结算'''

        mes = ''

        # 体力和气力恢复
        if sleep:
            sleep_minutes = self.time_manager.get_sleep_time()
            sleep_hours = sleep_minutes // 60

            # 体力和气力恢复，按8小时为满值恢复
            current_stamina = self.player.stamina
            current_energy = self.player.energy
            self.change_stamina(self.player.max_stamina * sleep_hours // 8)
            self.change_energy(self.player.max_energy * sleep_hours // 8)
            mes += f'{self.player.name}睡了一觉\n'
            mes += f'体力+{self.player.stamina - current_stamina}, 气力+{self.player.energy - current_energy}\n'

            self.time_manager.to_next_day()  # 推进到第二天

        elif exhaustion:
            # 体力耗尽结算，推进到体力和气力恢复到最大值的时间
            mes += f'\n{self.player.name}因为体力耗尽昏了过去……\n'
            exhaustion_minutes = self.time_manager.get_exhaustion_time()
            self.time_manager.advance_time(exhaustion_minutes)

            self.change_stamina(self.player.max_stamina)
            self.change_energy(self.player.max_energy)

            mes += f'强制休息了一段时间……\n'

        # 根据工作量结算金钱
        if self.work_manager.works_done > 0:
            self.player.set_money(self.player.money + self.work_manager.works_done)  # 奖励完成的工作量的钱
            mes += f'今日完成了{self.work_manager.works_done}工作量，{self.player.name}获得了{self.work_manager.works_done}金钱奖励……\n'

        # 检查工作量是否完成
        if self.work_manager.works > 0:
            # 有未完成的工作会扣钱
            self.player.set_money(self.player.money - self.work_manager.works)  # 扣除工作量的钱
            mes += f'由于未完成的工作，{self.player.name}被罚了{self.work_manager.works}金钱……\n'

        # 生成新的一天的工作量
        self.work_manager.set_works()
        self.work_manager.works_done = 0  # 重置已完成工作量
        mes += f'又有了新的工作……今天的工作量是{self.work_manager.works}'

        return mes
