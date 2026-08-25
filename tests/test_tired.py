# -*- coding: utf-8 -*-
"""疲倦系统测试：疲倦判定、扣减、玩家归零日结、舰娘归零休息、调教交互"""


def _set_time(world, hour, minute=0):
    world.time_manager.hour = hour
    world.time_manager.minute = minute


def _make_train(world, actors=('player',), targets=('javelin',)):
    from game_engine.managers.TrainManager import Train
    train = Train(world.player.location, world.player)
    train.actors = list(actors)
    train.targets = list(targets)
    train.participants = list(actors) + list(targets)
    world.train_manager.train = train
    world.train_mode = True
    return train


class TestTiredFlag:
    """疲倦判定"""

    def test_player_tired_after_15h(self, world):
        # 起床 7:00 → 21:59 未疲倦，22:00 疲倦
        _set_time(world, 21)
        world._update_tired_flag(world.player)
        assert world.player.cflag['tired'] is False
        _set_time(world, 22)
        world._update_tired_flag(world.player)
        assert world.player.cflag['tired'] is True

    def test_tired_crosses_midnight(self, world):
        # 改起床时间为 23:00 → 次 13:59 未疲倦，14:00 疲倦（跨午夜）
        world.player.wake_time = {'hour': 23, 'minute': 0}
        _set_time(world, 13)
        world._update_tired_flag(world.player)
        assert world.player.cflag['tired'] is False
        _set_time(world, 14)
        world._update_tired_flag(world.player)
        assert world.player.cflag['tired'] is True

    def test_npc_wake_from_schedule(self, world):
        # 标枪睡 23:00-8:00，起床 8:00 → 22:59 未疲倦，23:00 疲倦
        javelin = world.npc_manager.shipgirls['javelin']
        _set_time(world, 22, 59)
        world._update_tired_flag(javelin)
        assert javelin.cflag['tired'] is False
        _set_time(world, 23)
        world._update_tired_flag(javelin)
        assert javelin.cflag['tired'] is True


class TestTiredDrain:
    """疲倦扣减与豁免"""

    def test_drain_per_minute(self, world):
        _set_time(world, 22)
        world.player.set_stamina(500)
        world.player.set_energy(500)
        world.advance_time_with_events(10)
        assert world.player.get_stamina() == 490
        assert world.player.get_energy() == 490

    def test_no_drain_before_tired(self, world):
        _set_time(world, 21)
        world.player.set_stamina(500)
        world.advance_time_with_events(10)
        assert world.player.get_stamina() == 500

    def test_sleeping_npc_exempt(self, world):
        # 标枪疲倦时段恰为睡觉时段：睡觉中不扣减
        javelin = world.npc_manager.shipgirls['javelin']
        _set_time(world, 23)
        javelin.set_stamina(500)
        javelin.set_energy(500)
        world.advance_time_with_events(10)
        assert javelin.cflag['sleeping'] is True
        assert javelin.get_stamina() == 500

    def test_resting_exempt_and_recovers(self, world):
        javelin = world.npc_manager.shipgirls['javelin']
        world.npc_manager.set_loc('javelin', 'home', 'living_room')
        world._start_rest(javelin)
        javelin.set_stamina(300)
        javelin.set_energy(300)
        _set_time(world, 12)  # 白天，无睡觉干扰
        world.advance_time_with_events(10)
        # 每分钟恢复 max 的1%（体力1500→15/分钟），且不被疲倦扣减
        assert javelin.get_stamina() == 450
        assert javelin.get_energy() == 450

    def test_rest_clears_when_full(self, world):
        javelin = world.npc_manager.shipgirls['javelin']
        world._start_rest(javelin)
        javelin.set_stamina(javelin.base['max_stamina'])
        javelin.set_energy(javelin.base['max_energy'])
        world._rest_recover(0)
        assert javelin.cflag['resting'] is False


class TestPlayerExhaustionByTired:
    """玩家疲倦归零触发昏倒日结"""

    def test_zero_triggers_settle(self, world, monkeypatch):
        # 存量bug：exp2abl KeyError 会炸所有日结路径，与本测试无关，隔离开
        import world as world_mod
        monkeypatch.setattr(world_mod, 'abl_lv_process', lambda chara, defs: [])
        _set_time(world, 22)
        world.player.set_stamina(5)
        world.menu_active = False
        world.advance_time_with_events(10)
        assert world.menu_active is True  # 日结后回到缓冲菜单
        assert world.player.get_stamina() == world.player.base['max_stamina']
        assert world.player.cflag['tired'] is False  # 时间跳到次日起床点，疲倦解除


class TestNpcRest:
    """舰娘归零回家休息"""

    def test_daily_zero_goes_home_resting(self, world):
        javelin = world.npc_manager.shipgirls['javelin']
        world.npc_manager.set_loc('javelin', 'shop_street', 'shop')
        javelin.set_stamina(100)
        _set_time(world, 12)
        pages = world.npc_exhausted(javelin)
        assert any('休息' in p for p in pages)
        assert javelin.cflag['resting'] is True
        # 回到了家（标枪卧室）
        assert javelin.location == {'region': 'royal_dorm', 'node': 'javelin_room'}

    def test_train_zero_forces_end(self, world):
        _make_train(world)
        javelin = world.npc_manager.shipgirls['javelin']
        javelin.set_stamina(5)
        _set_time(world, 20)  # 疲倦时段外，仅指令消耗致归零
        world.advance_time_with_events(0)  # 触发一次调度初始化
        pages = world.npc_exhausted(javelin)
        assert any('调教被迫结束' in p for p in pages)
        assert world.train_mode is False
        assert world.train_manager.train is None
        assert javelin.cflag['resting'] is True


class TestTrainSleepGuard:
    """调教中忽略睡觉，结束后立即重新调度"""

    def test_no_sleep_during_train(self, world):
        _make_train(world)
        javelin = world.npc_manager.shipgirls['javelin']
        world.npc_manager.set_loc('javelin', 'home', 'living_room')
        _set_time(world, 23, 30)  # 标鸡睡觉时段内
        world.advance_time_with_events(5)
        # 不被标记睡觉、不被送回卧室
        assert javelin.cflag['sleeping'] is False
        assert javelin.location == {'region': 'home', 'node': 'living_room'}

    def test_reschedule_after_end_train(self, world):
        _make_train(world)
        javelin = world.npc_manager.shipgirls['javelin']
        world.npc_manager.set_loc('javelin', 'home', 'living_room')
        _set_time(world, 23, 30)
        world.advance_time_with_events(5)
        world.train_manager.end_train()
        # 结束后立即按当前时间调度：回家睡觉
        assert javelin.cflag['sleeping'] is True
        assert javelin.location == {'region': 'royal_dorm', 'node': 'javelin_room'}
