from config.abl_lv import abl_lv
from data.data_loader import load_attr_defs
from game_engine.commands._common import abl_lv_process
from game_engine.managers.CommandManager import CommandManager
from game_engine.managers.MapManager import MapManager
from game_engine.managers.NpcManager import NpcManager
from game_engine.managers.TimeManager import TimeManager
from game_engine.managers.WorkManager import WorkManager
from game_engine.models.player import Player


class World:
    def __init__(self):
        self.attr_defs = load_attr_defs()
        self.player = Player()
        self.map_manager = MapManager()
        self.npc_manager = NpcManager()
        self.work_manager = WorkManager()
        self.time_manager = TimeManager(self.player, self.npc_manager, self.map_manager)
        self.command_manager = CommandManager(self)

    def get_state(self):
        '''一次性返回前端需要的全部状态'''
        r, n = self.player.location['region'], self.player.location['node']
        return {
            'player': self.player.get_state(),
            'location': self.map_manager.get_current_loc(self.player),
            'act_com': self.command_manager.get_Act_COM(),
            'ex_com': self.command_manager.get_EX_COM(),
            'time': self.time_manager.get_state(),
            'nearby_npcs': [sg.get_state() for sg in self.npc_manager.get_npcs_at(r, n)],
            'palam_defs': {k: v['name'] for k, v in self.attr_defs['palam'].items()},
        }

    def advance_time_with_events(self, minutes: int):
        '''推进时间并返回玩家附近舰娘的变动消息（委托给 TimeManager）'''
        return self.time_manager.advance_time_with_events(minutes)

    def change_stamina(self, delta: int):
        '''包装一层改变体力的方法
        返回字符串（耗尽时直接把结算拼进来，不破坏调用处的拼接逻辑）'''
        exhaustion = not self.player.set_stamina(self.player.get_stamina() + delta)
        if exhaustion:
            pages = self.settle_day(exhaustion=True)
            return '\n'.join(pages)
        return ''
    
    def change_energy(self, delta: int):
        '''包装一层改变气力的方法'''
        exhaustion = not self.player.set_energy(self.player.get_energy() + delta)
        if exhaustion:
            # TODO: 后续做气力为0的影响
            pass
        return ''

    def settle_day(self, sleep: bool = False, exhaustion: bool = False):
        '''日终结算 
        sleep: 是否是睡觉结算
        exhaustion: 是否是体力耗尽结算
        返回: 翻页文本列表'''

        pages = []

        # 体力和气力恢复
        if sleep:
            sleep_minutes = self.time_manager.get_sleep_time()
            sleep_hours = sleep_minutes // 60

            # 体力和气力恢复，按8小时为满值恢复
            current_stamina = self.player.get_stamina()
            current_energy = self.player.get_energy()
            self.change_stamina(self.player.base['max_stamina'] * sleep_hours // 8)
            self.change_energy(self.player.base['max_energy'] * sleep_hours // 8)
            pages.append(f'{self.player.name}准备睡觉……')
            pages.append(f'睡了一觉（{sleep_hours}小时）\n体力+{self.player.get_stamina() - current_stamina}　气力+{self.player.get_energy() - current_energy}')

            self.time_manager.to_next_day()  # 推进到第二天
            # 更新舰娘到新时间的位置（起床后的调度）
            self.npc_manager.update_positions(self.time_manager.hour, 0, self.map_manager)

        elif exhaustion:
            # 体力耗尽结算，推进到体力和气力恢复到最大值的时间
            pages.append(f'{self.player.name}因为体力耗尽昏了过去……')
            exhaustion_minutes = self.time_manager.get_exhaustion_time()
            self.time_manager.advance_time(exhaustion_minutes)

            self.change_stamina(self.player.base['max_stamina'])
            self.change_energy(self.player.base['max_energy'])

            pages.append(f'强制休息了一段时间，恢复了全部体力与气力')

        # 根据工作量结算金钱
        if self.work_manager.works_done > 0:
            self.player.set_money(self.player.money + self.work_manager.works_done)  # 奖励完成的工作量的钱
            pages.append(f'今日完成了{self.work_manager.works_done}工作量，获得{self.work_manager.works_done}金钱奖励')

        # 检查工作量是否完成
        if self.work_manager.works > 0:
            # 有未完成的工作会扣钱
            self.player.set_money(self.player.money - self.work_manager.works)  # 扣除工作量的钱
            pages.append(f'由于未完成的工作，被罚了{self.work_manager.works}金钱')

        # 检查所有角色的exp是否达到升级条件，若达到则升级
        for npc in self.npc_manager.get_all_npcs():
            mes = abl_lv_process(npc, self.attr_defs)
            if mes:
                pages.append(mes)
        mes = abl_lv_process(self.player, self.attr_defs)
        if mes:
            pages.append(mes)
        
        # 生成新的一天的工作量
        self.work_manager.set_works()
        self.work_manager.works_done = 0  # 重置已完成工作量
        pages.append(f'又有了新的工作……今天的工作量是{self.work_manager.works}')

        return pages

