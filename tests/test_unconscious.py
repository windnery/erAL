# -*- coding: utf-8 -*-
"""调教中舰娘气力归零进入"神志不清"状态：
主导权强制归0、不再增长、调教结束时解除"""


class TestUnconscious:
    @staticmethod
    def _start_train(world):
        world.train_manager.new_train(
            participants=['player', 'laffey'],
            initiative={'player': 100, 'laffey': 50},
        )
        return world.npc_manager.shipgirls['laffey']

    @staticmethod
    def _ctx(world):
        from game_engine.commands._context import CommandContext
        return CommandContext(world)

    def test_attr_defs_has_default(self, npcs):
        """attr_defs 定义打底：加载后所有舰娘都带该cflag且默认False"""
        assert all(sg.cflag.get('unconscious') is False for sg in npcs.values())

    def test_energy_zero_in_train_triggers(self, world):
        """调教中目标气力归0：设flag + 主导权归0"""
        laffey = self._start_train(world)
        laffey.set_energy(50)
        ctx = self._ctx(world)
        ctx.consume(energy=100, chara=laffey)
        mes = '\n'.join(ctx.result())
        assert laffey.cflag['unconscious'] is True
        assert world.train_manager.train.initiative['laffey'] == 0
        assert '神志不清' in mes

    def test_energy_zero_outside_train_not_trigger(self, world):
        """非调教状态气力归0不触发"""
        laffey = self._start_train(world)
        world.train_manager.end_train()
        laffey.set_energy(50)
        self._ctx(world).consume(energy=100, chara=laffey)
        assert laffey.cflag['unconscious'] is False

    def test_actor_side_not_trigger(self, world):
        """调教者侧（非target）气力归0不触发"""
        z23 = world.npc_manager.shipgirls['Z23']
        world.train_manager.new_train(
            participants=['player', 'Z23'],
            initiative={'player': 0, 'Z23': 0},
        )
        # 把Z23切到actor侧
        world.train_manager.toggle_target('Z23')
        world.train_manager.toggle_actor('Z23')
        z23.set_energy(50)
        self._ctx(world).consume(energy=100, chara=z23)
        assert z23.cflag['unconscious'] is False

    def test_no_growth_when_unconscious(self, world):
        """神志不清时主导权不再增长"""
        laffey = self._start_train(world)
        laffey.set_energy(50)
        self._ctx(world).consume(energy=100, chara=laffey)

        from game_engine.data_pipeline.initiative_calc import initiative_grow_proc
        train = world.train_manager.train
        mes = initiative_grow_proc(train, [(laffey, 0)])
        assert mes == []
        assert train.initiative['laffey'] == 0

    def test_end_train_clears_flag(self, world):
        """调教结束解除神志不清"""
        laffey = self._start_train(world)
        laffey.set_energy(50)
        self._ctx(world).consume(energy=100, chara=laffey)
        assert laffey.cflag['unconscious'] is True
        world.train_manager.end_train()
        assert laffey.cflag['unconscious'] is False
