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
    """update_positions(hour, minutes, map_manager, player)"""

    def _call(self, world, hour, minutes=0):
        world.npc_manager.update_positions(
            hour, minutes, world.map_manager, world.player)

    def test_sleeping_returns_home(self, world):
        """睡觉时间舰娘回初始位置并 sleeping=True"""
        z23 = world.npc_manager.shipgirls['Z23']
        # 先移到别处
        world.npc_manager.set_loc('Z23', 'canteen', 'canteen_1')
        self._call(world, hour=23, minutes=30)
        assert z23.cflag['sleeping'] is True
        assert z23.location == world.npc_manager.shipgirls_db['Z23']['location']

    def test_awake_not_sleeping(self, world):
        """白天不睡觉"""
        z23 = world.npc_manager.shipgirls['Z23']
        self._call(world, hour=12, minutes=0)
        assert z23.cflag.get('sleeping') is False

    def test_secretary_follows_player(self, world):
        """秘书舰跟随玩家位置"""
        z23 = world.npc_manager.shipgirls['Z23']
        world.npc_manager.set_secretary_ship_proc('Z23', world.player)
        # 玩家移动
        world.player.location = {'region': 'home', 'node': 'bedroom'}
        self._call(world, hour=10, minutes=0)
        # 秘书舰 18:00 前跟随 → 应到玩家位置
        assert z23.location == world.player.location

    def test_secretary_stops_following_after_18(self, world):
        """秘书舰 18:00 后取消跟随"""
        z23 = world.npc_manager.shipgirls['Z23']
        world.npc_manager.set_secretary_ship_proc('Z23', world.player)
        world.player.location = {'region': 'home', 'node': 'bedroom'}
        self._call(world, hour=19, minutes=0)
        assert z23.cflag.get('secretary_ship_following') is False

    def test_dating_timeout_calls_end_date(self, world):
        """约会舰娘 21:00 后自动结束约会"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.cflag['dating'] = True
        z23.cflag['dating_following'] = True
        self._call(world, hour=21, minutes=30)
        assert z23.cflag.get('dating') is False

    def test_dating_before_21_still_dating(self, world):
        """21:00 前约会不结束"""
        z23 = world.npc_manager.shipgirls['Z23']
        z23.cflag['dating'] = True
        self._call(world, hour=20, minutes=0)
        assert z23.cflag.get('dating') is True

    def test_working_goes_to_workplace(self, world):
        """工作时间舰娘去工作地点"""
        z23 = world.npc_manager.shipgirls['Z23']
        # Z23 默认 schedule.work 为空，构造一个
        z23.schedule['work'] = {
            'location': {'region': 'office', 'node': 'office_1'},
            'time': [[9, 17]]
        }
        self._call(world, hour=10, minutes=0)
        assert z23.cflag.get('working') is True
        assert z23.location['region'] == 'office'


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
