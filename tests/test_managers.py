# -*- coding: utf-8 -*-
"""第三层：管理器集成测试

覆盖：update_positions 调度、settle_day 全流程、存档读档一致性
"""
import pytest

from conftest import place_next_to_player


# ============================================================
# update_positions 舰娘调度
# ============================================================

class TestUpdatePositions:
    """update_positions(elapsed_minutes, map_manager, player)
    当前时间从 world.time_manager 读取（方案 B）
    """

    def _set_time(self, world, hour, minute=0):
        """设置 time_manager 的当前时间"""
        world.time_manager.hour = hour
        world.time_manager.minute = minute

    def _call(self, world, hour, minute=0, elapsed=0):
        """设置时间后调用 update_positions
        hour/minute: 当前时间（写入 time_manager）
        elapsed: 本次推进的分钟数（自由行动概率用）
        """
        self._set_time(world, hour, minute)
        world.npc_manager.update_positions(
            elapsed, world.map_manager, world.player)

    def test_sleeping_returns_home(self, world):
        """睡觉时间舰娘回初始位置并 sleeping=True"""
        z23 = world.npc_manager.shipgirls['Z23']
        # 先移到别处
        world.npc_manager.set_loc('Z23', 'canteen', 'canteen_1')
        self._call(world, hour=23, minute=30)
        assert z23.cflag['sleeping'] is True
        assert z23.location == world.npc_manager.shipgirls_db['Z23']['location']

    def test_awake_not_sleeping(self, world):
        """白天不睡觉"""
        z23 = world.npc_manager.shipgirls['Z23']
        self._call(world, hour=12, minute=0)
        assert z23.cflag.get('sleeping') is False

    def test_secretary_follows_player(self, world):
        """秘书舰跟随玩家位置"""
        z23 = world.npc_manager.shipgirls['Z23']
        world.npc_manager.set_secretary_ship_proc('Z23', world.player)
        # 玩家移动
        world.player.location = {'region': 'home', 'node': 'bedroom'}
        self._call(world, hour=10, minute=0)
        # 秘书舰 18:00 前跟随 → 应到玩家位置
        assert z23.location == world.player.location

    def test_secretary_stops_following_after_18(self, world):
        """秘书舰 18:00 后取消跟随"""
        z23 = world.npc_manager.shipgirls['Z23']
        world.npc_manager.set_secretary_ship_proc('Z23', world.player)
        world.player.location = {'region': 'home', 'node': 'bedroom'}
        self._call(world, hour=19, minute=0)
        assert z23.cflag.get('secretary_ship_following') is False

    def test_dating_timeout_calls_end_date(self, world):
        """约会舰娘 21:00 后自动结束约会"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.cflag['dating'] = True
        z23.cflag['dating_following'] = True
        self._call(world, hour=21, minute=30)
        assert z23.cflag.get('dating') is False

    def test_dating_before_21_still_dating(self, world):
        """21:00 前约会不结束"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.cflag['dating'] = True
        self._call(world, hour=20, minute=0)
        assert z23.cflag.get('dating') is True

    def test_working_goes_to_workplace(self, world):
        """工作时间舰娘去工作地点（新 works 结构）"""
        z23 = world.npc_manager.shipgirls['Z23']
        # Z23 默认 works 为空，构造一个
        z23.schedule['works'] = [{
            'desc': '测试工作',
            'location': {'region': 'office', 'node': 'desk'},
            'time': {'start': [9, 0], 'end': [17, 0]}
        }]
        self._call(world, hour=10, minute=0)
        assert z23.cflag.get('working') is True
        assert z23.location['region'] == 'office'
        assert z23.location['node'] == 'desk'

    def test_works_empty_clears_working(self, world):
        """回归 Bug C：works 为空时 working 被重置 False"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.schedule['works'] = []
        z23.cflag['working'] = True  # 模拟残留
        self._call(world, hour=10, minute=0)
        assert z23.cflag.get('working') is False

    def test_works_outside_all_periods_clears_working(self, world):
        """多个 works 时段都不在当前时间 → working False"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.schedule['works'] = [
            {'desc': '早班', 'location': {'region': 'office', 'node': 'desk'},
             'time': {'start': [9, 0], 'end': [12, 0]}},
            {'desc': '晚班', 'location': {'region': 'canteen', 'node': 'hall'},
             'time': {'start': [18, 0], 'end': [21, 0]}}
        ]
        z23.cflag['working'] = True  # 模拟残留
        self._call(world, hour=14, minute=0)
        assert z23.cflag.get('working') is False

    def test_works_second_period_hit(self, world):
        """多个 works 时段命中第二个"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.schedule['works'] = [
            {'desc': '早班', 'location': {'region': 'office', 'node': 'desk'},
             'time': {'start': [9, 0], 'end': [12, 0]}},
            {'desc': '晚班', 'location': {'region': 'canteen', 'node': 'hall'},
             'time': {'start': [18, 0], 'end': [21, 0]}}
        ]
        self._call(world, hour=19, minute=0)
        assert z23.cflag.get('working') is True
        assert z23.location['region'] == 'canteen'

    def test_work_end_hour_boundary(self, world):
        """半开区间：17:00 整点下班"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.schedule['works'] = [{
            'desc': '测试工作',
            'location': {'region': 'office', 'node': 'desk'},
            'time': {'start': [9, 0], 'end': [17, 0]}
        }]
        self._call(world, hour=17, minute=0)
        assert z23.cflag.get('working') is False

    def test_work_same_hour_period(self, world):
        """回归 Bug A：同小时时段 9:00-9:30，9:30 应下班"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.schedule['works'] = [{
            'desc': '短班',
            'location': {'region': 'office', 'node': 'desk'},
            'time': {'start': [9, 0], 'end': [9, 30]}
        }]
        # 9:15 上班中
        self._call(world, hour=9, minute=15)
        assert z23.cflag.get('working') is True
        # 9:30 整点下班
        self._call(world, hour=9, minute=30)
        assert z23.cflag.get('working') is False

    def test_work_overnight_requires_night_sleep_schedule(self, world):
        """跨天夜班：当前睡觉判断不支持白天睡作息

        现状：睡觉判断隐含假设晚上睡（sleep < wake）。
        若舰娘排 22:00-2:00 夜班但作息是晚上睡（23:00-7:00），
        23:00 后睡觉判断优先 → 回家睡觉。
        这是设计约束：夜班数据要配白天睡作息，但白天睡作息当前不被
        睡觉判断支持 → 夜班暂不可用，测试记录现状。
        """
        z23 = world.npc_manager.shipgirls['Z23']
        z23.schedule['works'] = [{
            'desc': '夜班',
            'location': {'region': 'shop_street', 'node': 'shop'},
            'time': {'start': [22, 0], 'end': [2, 0]}
        }]
        # 22:30 未到睡觉时间 → 正常上班
        self._call(world, hour=22, minute=30)
        assert z23.cflag.get('working') is True
        # 23:30 已到睡觉时间 → 睡觉优先，回家（夜班被睡觉打断）
        self._call(world, hour=23, minute=30)
        assert z23.cflag.get('sleeping') is True
        assert z23.cflag.get('working') is False

    def test_in_work_overnight_math(self):
        """_in_work 跨天时段数学正确（不依赖舰娘作息）"""
        from game_engine.managers.NpcManager import _in_work
        assert _in_work(23, 30, [22, 0], [2, 0]) is True
        assert _in_work(1, 0, [22, 0], [2, 0]) is True
        assert _in_work(2, 0, [22, 0], [2, 0]) is False
        assert _in_work(21, 59, [22, 0], [2, 0]) is False

    def test_current_minute_from_time_manager(self, world):
        """回归 minutes 语义：当前分钟读 time_manager，推进量不影响工作判断

        场景：玩家 7:50 执行 30 分钟指令 → 当前 8:20
        明石 8:30 上班，8:20 不应 working（旧代码 minutes=30 会误判上班）
        """
        akashi = world.npc_manager.shipgirls['akashi']
        # 明石默认 works: 8:30-19:30
        self._set_time(world, 8, 20)
        world.npc_manager.update_positions(30, world.map_manager, world.player)
        assert akashi.cflag.get('working') is False, '8:20 未到 8:30 不应上班'
        # 同一时刻传入不同 elapsed 不应改变结果
        self._set_time(world, 8, 20)
        world.npc_manager.update_positions(0, world.map_manager, world.player)
        assert akashi.cflag.get('working') is False


# ============================================================
# settle_day 日终结算全流程
# ============================================================

class TestSettleDay:
    def test_settle_day_runs_full_pipeline(self, world):
        """日终结算：不崩 + 状态重置 + 菜单激活"""
        # 给点数据触发管线
        z23 = world.npc_manager.shipgirls['Z23']
        z23.palam['c_pleasure_palam'] = 5000
        z23.palam['kindness_palam'] = 1000
        world.player.palam['c_pleasure_palam'] = 2000

        pages = world.settle_day(sleep=False, exhaustion=False)
        assert isinstance(pages, list)
        # palam 清空
        assert all(v == 0 for v in z23.palam.values())
        assert all(v == 0 for v in world.player.palam.values())
        # juel 增加
        assert z23.juel['c_pleasure_juel'] > 0
        # 菜单激活
        assert world.menu_active is True
        # 新工作量生成
        assert world.work_manager.works > 0

    def test_settle_day_sleep_recovers_stamina(self, world):
        """睡觉结算恢复体力（睡 8 小时 = max）"""
        world.player.base['stamina'] = 0
        world.player.base['energy'] = 0
        world.player.location = {'region': 'home', 'node': 'bedroom'}
        # 23:00 睡到 7:00 = 8 小时
        world.time_manager.hour = 23
        world.time_manager.minute = 0
        world.player.wake_time = {'hour': 7, 'minute': 0}
        pages = world.settle_day(sleep=True)
        assert world.player.get_stamina() > 0
        assert world.time_manager.hour == 7
        assert world.time_manager.day == 2

    def test_settle_day_exhaustion_recovers_all(self, world):
        """体力耗尽结算：全恢复 + 时间推进"""
        world.player.base['stamina'] = 0
        world.player.base['energy'] = 50
        pages = world.settle_day(sleep=False, exhaustion=True)
        assert world.player.get_stamina() == world.player.base['max_stamina']
        assert world.player.get_energy() == world.player.base['max_energy']

    def test_work_done_rewards_money(self, world):
        """完成工作奖励金钱，未完成扣钱（set_money 防负钳制）"""
        world.work_manager.works = 1000
        world.work_manager.works_done = 300
        world.player.money = 2000  # 足够扣
        money_before = world.player.money
        world.settle_day()
        assert world.player.money == money_before + 300 - 1000

    def test_money_never_negative(self, world):
        """金钱不会扣成负数（set_money 钳制）"""
        world.work_manager.works = 1000
        world.work_manager.works_done = 0
        world.player.money = 0
        world.settle_day()
        assert world.player.money == 0

    def test_talent_check_runs(self, world):
        """日终 talent 检查执行（relationship 升级）"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.favor = 900
        z23.trust = 200
        z23.abl['intimacy_abl'] = 5
        z23.set_talent('relationship', '0')
        pages = world.settle_day()
        assert z23.get_talent_value('relationship') >= 1


# ============================================================
# 存档读档
# ============================================================

class TestSaveLoad:
    def test_save_then_load_roundtrip(self, world, tmp_path):
        """存档→读档：关键状态一致"""
        # 制造状态
        z23 = world.npc_manager.shipgirls['Z23']
        z23.favor = 777
        z23.cflag['dating'] = True
        z23.palam['c_pleasure_palam'] = 3000
        z23.abl['talk_abl'] = 2
        world.player.money = 500
        world.npc_manager.set_secretary_ship_proc('Z23', world.player)
        world.time_manager.day = 3
        world.time_manager.hour = 15
        world.work_manager.works = 1111

        # 存
        world.save_manager.sav_dir = tmp_path
        world.save_manager.save_game(1)

        # 全新世界读档
        from world import World
        world2 = World()
        world2.save_manager.sav_dir = tmp_path
        err = world2.save_manager.load_game(1)
        assert err is None, f'读档失败: {err}'

        # 校验
        z23b = world2.npc_manager.shipgirls['Z23']
        assert z23b.favor == 777
        assert z23b.cflag.get('dating') is True
        assert z23b.abl['talk_abl'] == 2
        assert world2.player.money == 500
        assert world2.time_manager.day == 3
        assert world2.time_manager.hour == 15
        assert world2.work_manager.works == 1111
        assert world2.npc_manager.secretary_ship.id == 'Z23'
        # palam_lv 从 palam 重建（3000 ≥ 2000 且 < 5000 → 5 级）
        assert z23b.palam_lv['c_pleasure_palam'] == 5

    def test_load_empty_slot_returns_error(self, world, tmp_path):
        """空槽位读档返回错误信息"""
        world.save_manager.sav_dir = tmp_path
        err = world.save_manager.load_game(2)
        assert err is not None

    def test_get_save_list(self, world, tmp_path):
        """槽位列表"""
        world.save_manager.sav_dir = tmp_path
        lst = world.save_manager.get_save_list()
        assert len(lst) == 3
        assert all(not e['has_save'] for e in lst)


class TestSaveLoadV2:
    """v2 存档：皮肤系统 + 道具系统 roundtrip + 版本迁移"""

    def test_save_then_load_skins_and_items(self, world, tmp_path):
        """存档→读档：皮肤购买/穿戴 + 背包道具一致"""
        # 制造皮肤/道具状态
        world.skin_manager.gain_skin('snow_rabbit_and_candy_apple')
        world.skin_manager.locked_skins.discard('snow_rabbit_and_candy_apple')
        world.skin_manager.equip_skin('laffey', 'snow_rabbit_and_candy_apple')
        world.item_manager.gain_items('oath_ring', 2)

        world.save_manager.sav_dir = tmp_path
        world.save_manager.save_game(1)

        from world import World
        world2 = World()
        world2.save_manager.sav_dir = tmp_path
        err = world2.save_manager.load_game(1)
        assert err is None, f'读档失败: {err}'

        # 皮肤：已购买 + 穿戴
        assert 'snow_rabbit_and_candy_apple' in world2.skin_manager.unlocked_skins
        assert 'snow_rabbit_and_candy_apple' not in world2.skin_manager.locked_skins
        assert world2.skin_manager.ships_wear_skin['laffey'] == 'snow_rabbit_and_candy_apple'
        # 道具
        assert world2.item_manager.items.get('oath_ring') == 2

    def test_v1_save_migrates_to_v2(self, world, tmp_path):
        """v1 旧档（无 skins/items 键）读档不崩，补默认空值"""
        # 构造 v1 存档（手动去掉 skins/items）
        world.save_manager.sav_dir = tmp_path
        data = world.save_manager.serialize_world()
        data['version'] = 1
        del data['data']['skins']
        del data['data']['items']
        import json
        path = tmp_path / 'slot_1.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

        from world import World
        world2 = World()
        world2.save_manager.sav_dir = tmp_path
        err = world2.save_manager.load_game(1)
        assert err is None, f'v1 迁移失败: {err}'
        # 默认空皮肤/道具
        assert world2.skin_manager.unlocked_skins == set()
        assert world2.skin_manager.locked_skins == set()
        assert world2.skin_manager.ships_wear_skin == {}
        assert world2.item_manager.items == {}

    def test_future_version_rejected(self, world, tmp_path):
        """版本过新的存档拒绝加载"""
        world.save_manager.sav_dir = tmp_path
        data = world.save_manager.serialize_world()
        data['version'] = 99
        import json
        path = tmp_path / 'slot_1.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

        from world import World
        world2 = World()
        world2.save_manager.sav_dir = tmp_path
        err = world2.save_manager.load_game(1)
        assert err is not None
        assert '版本过新' in err

    def test_save_version_is_2(self, world):
        """新存档版本号=2"""
        data = world.save_manager.serialize_world()
        assert data['version'] == 2
        assert 'skins' in data['data']
        assert 'items' in data['data']

    def test_save_then_load_shipgirl_talent(self, world, tmp_path):
        """舰娘 talent（含 relationship 陷落阶段）读档后保留"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.set_talent('relationship', '3')  # 爱
        z23.set_talent('lover', '1')

        world.save_manager.sav_dir = tmp_path
        world.save_manager.save_game(1)

        from world import World
        world2 = World()
        world2.save_manager.sav_dir = tmp_path
        err = world2.save_manager.load_game(1)
        assert err is None, f'读档失败: {err}'
        z23b = world2.npc_manager.shipgirls['Z23']
        assert z23b.talent.get('relationship') == '3'
        assert z23b.has_talent('lover')


# ============================================================
# 世界状态完整性
# ============================================================

class TestWorldState:
    def test_get_state_structure(self, world):
        """get_state 返回前端所需全部键"""
        st = world.get_state()
        for k in ('player', 'location', 'act_com', 'ex_com', 'menu_com',
                  'menu_active', 'time', 'nearby_npcs', 'cflag_defs',
                  'palam_defs', 'palam_lv_map'):
            assert k in st, f'缺少键 {k}'

    def test_get_state_nearby_npcs(self, world):
        """附近舰娘列表"""
        z23 = world.npc_manager.shipgirls['Z23']
        place_next_to_player(world, z23)
        st = world.get_state()
        ids = [n['id'] for n in st['nearby_npcs']]
        assert 'Z23' in ids

    def test_advance_time_with_events_returns_list(self, world):
        """推进时间返回事件列表"""
        events = world.advance_time_with_events(30)
        assert isinstance(events, list)

    def test_change_stamina_exhaustion_settles(self, world):
        """体力耗尽触发日终结算"""
        world.player.base['stamina'] = 5
        world.player.base['energy'] = 100
        world.work_manager.works = 0
        result = world.change_stamina(-10)
        # 体力清零 → 结算 → 返回结算文本
        assert result != ''


class TestTrainCommands:
    """调教指令通道：不进普通 act_com，由 TrainManager.get_train_commands 提供"""

    def _make_train(self, world, actors, targets):
        from game_engine.managers.TrainManager import Train
        world.train_manager.train = Train(world.player.location, world.player)
        world.train_manager.train.actors = list(actors)
        world.train_manager.train.targets = list(targets)

    def test_caress_not_in_act_com(self, world):
        """调教指令不进普通地点指令列表（无论是否有会话）"""
        keys = [c['key'] for c in world.command_manager.get_Act_COM()]
        assert 'caress' not in keys

        self._make_train(world, ['player', 'Z23'], ['laffey'])
        keys = [c['key'] for c in world.command_manager.get_Act_COM()]
        assert 'caress' not in keys

    def test_caress_not_in_npc_commands(self, world):
        """调教指令也不进选中舰娘的交互指令列表"""
        z23 = world.npc_manager.shipgirls['Z23']
        place_next_to_player(world, z23)
        keys = [c['key'] for c in world.command_manager.get_Act_COM('Z23')]
        assert 'caress' not in keys

    def test_get_train_commands_empty_without_session(self, world):
        """无调教会话时指令列表为空"""
        assert world.train_manager.get_train_commands() == []

    def test_get_train_commands_returns_caress(self, world):
        """会话人数达标时返回调教指令"""
        self._make_train(world, ['player', 'Z23'], ['laffey'])
        commands = world.train_manager.get_train_commands()
        assert [c['key'] for c in commands] == ['caress', 'end_train']
        assert commands[0]['name'] == '爱抚'
        assert commands[0]['cat'] == '爱抚'

    def test_get_train_commands_filters_by_can(self, world):
        """人数不满足 can 时指令被过滤（1 调教者 vs 1 被调教者）"""
        self._make_train(world, ['player'], ['Z23', 'laffey', 'javelin'])
        keys = [c['key'] for c in world.train_manager.get_train_commands()]
        assert 'caress' not in keys


    def test_train_manager_world_property(self, world):
        """TrainManager.world 属性指向同一 World"""
        assert world.train_manager.world is world
        assert world.train_manager.world is world.npc_manager.world

    def test_push_down_registered_and_enters_train(self, world, z23, player):
        """推倒成功：进入调教模式并建立会话"""
        place_next_to_player(world, z23)
        z23.set_talent('relationship', '1')
        z23.abl['intimacy_abl'] = 10
        z23.favor = 40000
        z23.trust = 900

        result = world.command_manager.do_cmd('push_down', 'Z23')
        assert isinstance(result, list)
        assert world.train_mode is True
        assert world.train_manager.train is not None
        assert world.train_manager.train.actors == ['player']
        assert world.train_manager.train.targets == ['Z23']

    def test_push_down_can_gate(self, world, z23, player):
        """亲密不足6时推倒不可用且不进入调教"""
        place_next_to_player(world, z23)
        z23.set_talent('relationship', '1')
        z23.abl['intimacy_abl'] = 5
        z23.favor = 1000

        from game_engine.commands.interact.push_down import can
        assert can(world, z23) is False
        assert world.command_manager.do_cmd('push_down', 'Z23') == ''
        assert world.train_mode is False

    def test_push_down_failure_does_not_enter_train(self, world, z23, player):
        """合意判定失败：负source惩罚，不进入调教"""
        place_next_to_player(world, z23)
        z23.set_talent('relationship', '1')
        z23.abl['intimacy_abl'] = 10
        z23.favor = 800
        z23.trust = 0
        player.abl['talk_abl'] = 0

        result = world.command_manager.do_cmd('push_down', 'Z23')
        assert isinstance(result, list)
        assert world.train_mode is False
        assert world.train_manager.train is None

    def test_end_train_registered_and_exits_mode(self, world):
        """结束调教：退出会话并复位模式"""
        world.train_manager.new_train(['player'], ['Z23'], {'player': 100, 'Z23': 0})
        assert world.train_mode is True

        result = world.command_manager.do_cmd('end_train')
        assert isinstance(result, list)
        assert world.train_mode is False
        assert world.train_manager.train is None

    def test_do_cmd_caress_via_command_manager(self, world, z23, player):
        """调教指令经 CommandManager 入口单参调用正常执行"""
        world.train_manager.new_train(['player'], ['Z23'], {'player': 100, 'Z23': 0})
        initial_energy = player.base['energy']

        result = world.command_manager.do_cmd('caress')
        assert isinstance(result, list)
        assert len(result) > 0
        # 玩家被消耗了体力和气力
        assert player.base['energy'] == initial_energy - 20
        # 关键：执行的是单参 func(world) 而非双参，不抛 TypeError

    def test_get_state_includes_train_mode(self, world):
        """get_state 返回调教模式状态与调教指令列表"""
        state = world.get_state()
        assert state['train_mode'] is False
        assert state['train_com'] == []

        world.train_manager.new_train(['player'], ['Z23'], {'player': 100, 'Z23': 0})
        state = world.get_state()
        assert state['train_mode'] is True
        keys = [c['key'] for c in state['train_com']]
        assert 'caress' in keys
        assert 'end_train' in keys
