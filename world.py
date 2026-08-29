from config.palam_config import PALAM_LV
from config.attr_defs import ATTR_DEFS
from game_engine.data_pipeline.abl.abl_lv_check import abl_lv_process
from game_engine.data_pipeline.juel.juel_calc import juel_calc
from game_engine.data_pipeline.mood.mood_calc import roll_daily_mood
from game_engine.data_pipeline.talent.talent_check import talent_check
from game_engine.managers.CommandManager import CommandManager
from game_engine.managers.EventManager import EventManager
from game_engine.managers.ItemManager import ItemManager
from game_engine.managers.MapManager import MapManager
from game_engine.managers.NpcManager import NpcManager
from game_engine.managers.SaveManager import SaveManager
from game_engine.managers.SkinManager import SkinManager
from game_engine.managers.TimeManager import TimeManager
from game_engine.managers.TrainManager import TrainManager
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
        self.event_manager = EventManager(self)
        self.skin_manager = SkinManager(self.npc_manager)
        self.item_manager = ItemManager(self.player)
        self.train_manager = TrainManager(self.npc_manager)
        # 缓冲菜单状态：游戏开始/每天日终后为 True，点“睁开眼睛”后为 False
        self.menu_active = True
        self.save_manager = SaveManager(self)
        # 日常/调教模式
        self.train_mode = False

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
            'act_com': self.command_manager.get_act_com(selected_npc_id),
            'ex_com': self.command_manager.get_ex_com(),
            'menu_com': self.command_manager.get_menu_com(),
            'menu_active': self.menu_active,
            'time': self.time_manager.get_state(),
            'nearby_npcs': nearby,
            'cflag_defs': ATTR_DEFS.get('cflag', {}),
            'palam_defs': {k: v['name'] for k, v in ATTR_DEFS.get('palam', {}).items()},
            'abl_defs': ATTR_DEFS.get('abl', {}),
            'exp_defs': ATTR_DEFS.get('exp', {}),
            'palam_lv_map': {str(k): v for k, v in PALAM_LV.items()},
            'train_mode': self.train_mode,
            'train_com': self.train_manager.get_train_commands(),
            'train_participants': self._get_train_participants(),
            'pending_choice': {
                'title': self.event_manager.pending_choice.title,
                'options': [
                    {'key': o.key, 'text': o.text, 'desc': o.desc}
                    for o in self.event_manager.pending_choice.options
                ]
            } if self.event_manager.pending_choice else None,
        }

    def _get_train_participants(self):
        """调教会话参与者信息（非训练态返回空列表）"""
        train = self.train_manager.train
        if not train:
            return []
        participants = []
        for chara_id in train.participants:
            is_player = chara_id == self.player.id
            if is_player:
                chara = self.player
                avatar = None
            else:
                chara = self.npc_manager.get_npc_by_id(chara_id)
                avatar = self.skin_manager.get_ship_skin_paths(chara_id)['avatar']
            participants.append({
                'id': chara_id,
                'name': chara.name,
                'avatar': avatar,
                'is_player': is_player,
                'initiative': train.initiative.get(chara_id, 0),
                'is_actor': chara_id in train.actors,
                'is_target': chara_id in train.targets,
            })
        return participants

    def advance_time_with_events(self, minutes: int):
        """推进时间并返回玩家附近舰娘的变动消息（委托给 TimeManager）
        随后结算休息恢复与疲倦扣减"""
        events = self.time_manager.advance_time_with_events(minutes)
        self._rest_recover(minutes)
        drain_pages = self._tired_drain(minutes)
        if drain_pages:
            events.extend(drain_pages)
        return events

    # ==================== 疲倦/休息 ====================
    TIRED_THRESHOLD_MINUTES = 15 * 60  # 距起床15小时进入疲倦
    REST_RECOVER_RATE = 0.01  # 休息中每分钟恢复1%

    def _wake_minute_of(self, chara) -> int:
        """角色的起床时刻（分钟数 0-1439）"""
        if isinstance(chara, Player):
            wt = chara.wake_time
        else:
            wt = {'hour': chara.schedule['sleep']['end'][0],
                  'minute': chara.schedule['sleep']['end'][1]}
        return wt['hour'] * 60 + wt['minute']

    def _update_tired_flag(self, chara):
        """按当前时间重算疲倦标志"""
        now = self.time_manager.hour * 60 + self.time_manager.minute
        elapsed = (now - self._wake_minute_of(chara)) % (24 * 60)
        chara.cflag['tired'] = elapsed >= self.TIRED_THRESHOLD_MINUTES

    def _tired_drain(self, minutes: int):
        """疲倦状态每分钟扣1点体力和气力；处理归零后果
        返回: 事件文本列表"""
        pages = []
        for chara in [self.player, *self.npc_manager.get_all_npcs()]:
            self._update_tired_flag(chara)
        for chara in [self.player, *self.npc_manager.get_all_npcs()]:
            if not chara.cflag.get('tired'):
                continue
            if chara.cflag.get('sleeping') or chara.cflag.get('resting'):
                continue
            chara.set_stamina(chara.get_stamina() - minutes)
            chara.set_energy(chara.get_energy() - minutes)

        # 玩家体力归零：昏倒日结
        if self.player.get_stamina() == 0:
            pages.extend(self.settle_day(exhaustion=True))
            return pages

        # 舰娘体力归零：回家休息（调教中被强制结束调教）
        for sg in self.npc_manager.get_all_npcs():
            if sg.get_stamina() > 0:
                continue
            if sg.cflag.get('resting') or sg.cflag.get('sleeping'):
                continue
            pages.extend(self.npc_exhausted(sg))
        return pages

    def npc_exhausted(self, sg):
        """舰娘体力归零的统一处理：
        调教中→强制结束调教；随后回家进入休息中"""
        pages = []
        if self.train_mode and self.train_manager.train and sg.id in self.train_manager.train.participants:
            pages.append(f'{sg.name}体力耗尽，无法继续……')
            self.train_manager.end_train()
            pages.append('本次调教被迫结束……')
        pages.append(f'{sg.name}回家休息了')
        self._start_rest(sg)
        return pages

    def _start_rest(self, sg):
        """舰娘进入休息中：回家，等待体力气力恢复"""
        sleep_loc = self.npc_manager.shipgirls_db[sg.id]['location']
        self.npc_manager.set_loc(sg.id, sleep_loc['region'], sleep_loc['node'])
        sg.cflag['resting'] = True
        sg.cflag['working'] = False

    def _rest_recover(self, minutes: int):
        """休息中的舰娘每分钟恢复1%体力和气力，双满后解除"""
        for sg in self.npc_manager.get_all_npcs():
            if not sg.cflag.get('resting') or sg.cflag.get('sleeping'):
                continue
            sta = max(1, int(sg.base['max_stamina'] * self.REST_RECOVER_RATE)) * minutes
            ene = max(1, int(sg.base['max_energy'] * self.REST_RECOVER_RATE)) * minutes
            sg.set_stamina(sg.get_stamina() + sta)
            sg.set_energy(sg.get_energy() + ene)
            if (sg.get_stamina() >= sg.base['max_stamina']
                    and sg.get_energy() >= sg.base['max_energy']):
                sg.cflag['resting'] = False

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

    def change_vitality(self, delta: int):
        """包装一层改变气力的方法"""
        self.player.set_vitality(self.player.get_vitality() + delta)
        return ''

    def is_training(self):
        """是否是调教模式"""
        return self.train_mode

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
            current_vitality = self.player.get_vitality()
            self.change_stamina(self.player.base['max_stamina'] * sleep_minutes // 480)
            self.change_energy(self.player.base['max_energy'] * sleep_minutes // 480)
            self.change_vitality(self.player.base.get('max_vitality', 2000) * sleep_minutes // 480)
            for npc in self.npc_manager.get_all_npcs():
                npc.set_stamina(npc.get_stamina() + npc.base['max_stamina'] * sleep_minutes // 480)
                npc.set_energy(npc.get_energy() + npc.base['max_energy'] * sleep_minutes // 480)
            pages.append(f'{self.player.name}准备睡觉……')
            pages.append(f'睡了一觉（{sleep_minutes // 60}时{sleep_minutes % 60}分）\n体力+{self.player.get_stamina() - current_stamina}　气力+{self.player.get_energy() - current_energy}　精力+{self.player.get_vitality() - current_vitality}')

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
            self.change_vitality(self.player.base.get('max_vitality', 2000))
            for npc in self.npc_manager.get_all_npcs():
                npc.set_stamina(npc.base['max_stamina'])
                npc.set_energy(npc.base['max_energy'])

            pages.append(f'强制休息了一段时间，恢复了全部体力与气力')
            # 体力耗尽也可能推进到深夜/次日，统一走调度，处理约会超时与舰娘回位
            self.npc_manager.update_positions(exhaustion_minutes, self.map_manager, self.player)

        # 重置当日已约会的状态
        for npc in self.npc_manager.get_all_npcs():
            if npc.cflag.get('dating_day', None) is not None and npc.cflag['dating_day'] < self.time_manager.day:
                npc.cflag['have_dated_today'] = False

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
            # 在这里重置每个舰娘的情绪、理性和新一天的心情 避免额外一次全遍历
            npc.reset_emotion()
            npc.reset_rationality()
            npc.set_mood(roll_daily_mood())

        # 生成新的一天的工作量
        self.work_manager.set_works()
        self.work_manager.works_done = 0  # 重置已完成工作量
        pages.append(f'又有了新的工作……今天的工作量是{self.work_manager.works}')

        # 新的一天开始：回到缓冲菜单
        self.menu_active = True

        # 时间已大幅推进：重算疲倦标志；体力已满的休息中舰娘解除休息
        for chara in [self.player, *self.npc_manager.get_all_npcs()]:
            self._update_tired_flag(chara)
        self._rest_recover(0)

        return pages

