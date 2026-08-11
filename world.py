from config.palam_lv import PALAM_LV
from config.attr_defs import ATTR_DEFS
from game_engine.data_pipeline.abl.abl_lv_check import abl_lv_process
from game_engine.data_pipeline.juel.juel_calc import juel_calc
from game_engine.data_pipeline.talent.talent_check import talent_check
from game_engine.managers.CommandManager import CommandManager
from game_engine.managers.ItemManager import ItemManager
from game_engine.managers.MapManager import MapManager
from game_engine.managers.NpcManager import NpcManager
from game_engine.managers.SaveManager import SaveManager
from game_engine.managers.SkinManager import SkinManager
from game_engine.managers.TimeManager import TimeManager
from game_engine.managers.WorkManager import WorkManager
from game_engine.models.player import Player


class World:
    def __init__(self):
        self.player = Player()
        self.map_manager = MapManager()
        self.npc_manager = NpcManager(self)
        self.work_manager = WorkManager()
        self.time_manager = TimeManager(self.player, self.npc_manager, self.map_manager)
        self.command_manager = CommandManager(self)
        self.skin_manager = SkinManager(self.npc_manager)
        self.item_manager = ItemManager(self.player)
        # 缓冲菜单状态：游戏开始/每天日终后为 True，点“睁开眼睛”后为 False
        self.menu_active = True
        self.save_manager = SaveManager(self)

    def get_state(self, selected_npc_id: str | None = None):
        """一次性返回前端需要的全部状态"""
        r, n = self.player.location['region'], self.player.location['node']
        nearby = []
        for sg in self.npc_manager.get_npcs_at(r, n):
            st = sg.get_state()
            # 当前穿戴皮肤的图片路径（下轮更换皮肤后即时生效）
            st['avatar'] = self.skin_manager.get_ship_skin_paths(sg.id)['avatar']
            st['portrait'] = self.skin_manager.get_ship_skin_paths(sg.id)['portrait']
            nearby.append(st)
        return {
            'player': self.player.get_state(),
            'location': self.map_manager.get_current_loc(self.player),
            'act_com': self.command_manager.get_Act_COM(selected_npc_id),
            'ex_com': self.command_manager.get_EX_COM(),
            'menu_com': self.command_manager.get_MENU_COM(),
            'menu_active': self.menu_active,
            'time': self.time_manager.get_state(),
            'nearby_npcs': nearby,
            'cflag_defs': {k: v['name'] for k, v in ATTR_DEFS.get('cflag', {}).items()},
            'palam_defs': {k: v['name'] for k, v in ATTR_DEFS.get('palam', {}).items()},
            'palam_lv_map': {str(k): v for k, v in PALAM_LV.items()},
        }

    def advance_time_with_events(self, minutes: int):
        """推进时间并返回玩家附近舰娘的变动消息（委托给 TimeManager）"""
        return self.time_manager.advance_time_with_events(minutes)

    def change_stamina(self, delta: int):
        """包装一层改变体力的方法
        返回字符串（耗尽时直接把结算拼进来，不破坏调用处的拼接逻辑）"""
        exhaustion = not self.player.set_stamina(self.player.get_stamina() + delta)
        if exhaustion:
            pages = self.settle_day(exhaustion=True)
            return '\n'.join(pages)
        return ''
    
    def change_energy(self, delta: int):
        """包装一层改变气力的方法"""
        self.player.set_energy(self.player.get_energy() + delta)
        return ''

    def settle_day(self, sleep: bool = False, exhaustion: bool = False):
        """日终结算 
        sleep: 是否是睡觉结算
        exhaustion: 是否是体力耗尽结算
        返回: 翻页文本列表"""

        pages = []

        # 体力和气力恢复
        if sleep:
            sleep_minutes = self.time_manager.get_sleep_time()

            # 体力和气力恢复，按8小时为满值恢复
            current_stamina = self.player.get_stamina()
            current_energy = self.player.get_energy()
            self.change_stamina(self.player.base['max_stamina'] * sleep_minutes // 480)
            self.change_energy(self.player.base['max_energy'] * sleep_minutes // 480)
            pages.append(f'{self.player.name}准备睡觉……')
            pages.append(f'睡了一觉（{sleep_minutes // 60}时{sleep_minutes % 60}分）\n体力+{self.player.get_stamina() - current_stamina}　气力+{self.player.get_energy() - current_energy}')

            self.time_manager.to_next_day()  # 推进到第二天
            # 更新舰娘到新时间的位置（起床后的调度）
            # 睡觉结算推进量大，但自由行动概率不需要动（睡觉时段所有人回家/睡觉）
            self.npc_manager.update_positions(0, self.map_manager, self.player)

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

        # 将palam转化为juel
        juel_calc(self.player)
        for npc in self.npc_manager.get_all_npcs():
            juel_calc(npc)
        # 清空当日palam
        self.player.clear_palam()
        for npc in self.npc_manager.get_all_npcs():
            npc.clear_palam()

        # 检查abl升级
        pages.extend(abl_lv_process(self.player, ATTR_DEFS))
        for npc in self.npc_manager.get_all_npcs():
            pages.extend(abl_lv_process(npc, ATTR_DEFS))

        # 检查talent
        for npc in self.npc_manager.get_all_npcs():
            pages.extend(talent_check(self, npc))
            # 在这里重置每个舰娘的情绪和理性 避免额外一次全遍历
            npc.reset_emotion()
            npc.reset_rationality()

        # 生成新的一天的工作量
        self.work_manager.set_works()
        self.work_manager.works_done = 0  # 重置已完成工作量
        pages.append(f'又有了新的工作……今天的工作量是{self.work_manager.works}')

        # 新的一天开始：回到缓冲菜单
        self.menu_active = True

        return pages

