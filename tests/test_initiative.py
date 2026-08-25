# -*- coding: utf-8 -*-
"""主导权链路测试：增长压制、射精整除3、绝顶衰减、批量结算挂接"""

from game_engine.data_pipeline.initiative_calc import (
    growth_delta,
    initiative_ejaculation_proc,
    initiative_grow_proc,
    initiative_orgasm_proc,
    pleasure_sum,
)
from config.initiative_config import INITIATIVE_BASE_GROWTH, INITIATIVE_S_MAX


class TestFormulas:
    """公式单测"""

    def test_pleasure_sum(self):
        src = {'c_pleasure_source': 100, 'v_pleasure_source': 50,
               'love_source': 999, 'm_pleasure_source': 30}
        assert pleasure_sum(src) == 180

    def test_growth_delta_boundaries(self):
        half = INITIATIVE_S_MAX // 2
        assert growth_delta(0) == INITIATIVE_BASE_GROWTH
        assert growth_delta(half) == int(INITIATIVE_BASE_GROWTH * 0.5)
        assert growth_delta(INITIATIVE_S_MAX - 1) == int(
            INITIATIVE_BASE_GROWTH * (1 - (INITIATIVE_S_MAX - 1) / INITIATIVE_S_MAX))
        assert growth_delta(INITIATIVE_S_MAX) == 0
        assert growth_delta(10 ** 9) == 0

    def test_ejaculation_decay(self, world):
        from game_engine.managers.TrainManager import Train
        train = Train(world.player.location, world.player)
        train.initiative = {world.player.id: 100}
        initiative_ejaculation_proc(train, world.player)
        assert train.initiative[world.player.id] == 100 // 2

    def test_ejaculation_decay_zero_no_message(self, world):
        from game_engine.managers.TrainManager import Train
        train = Train(world.player.location, world.player)
        train.initiative = {world.player.id: 1}
        assert initiative_ejaculation_proc(train, world.player) != ''
        assert train.initiative[world.player.id] == 0
        # 已为0时不再输出
        assert initiative_ejaculation_proc(train, world.player) == ''

    def test_orgasm_decay_by_lv_and_num(self, world):
        from game_engine.managers.TrainManager import Train
        from config.initiative_config import ORGASM_INITIATIVE_RATE_LV, ORGASM_INITIATIVE_MULT_NUM
        laffey = world.npc_manager.shipgirls['laffey']
        train = Train(world.player.location, world.player)
        # 单部位绝顶 lv1：按配置衰减率
        train.initiative = {laffey.id: 100}
        assert initiative_orgasm_proc(train, laffey, 1, 1) != ''
        expected = 100 - int(100 * ORGASM_INITIATIVE_RATE_LV[1] * ORGASM_INITIATIVE_MULT_NUM[1])
        assert train.initiative[laffey.id] == expected
        # 二重强绝顶 lv2 num2：等级系数 × 部位数乘数
        rate2 = ORGASM_INITIATIVE_RATE_LV[2] * ORGASM_INITIATIVE_MULT_NUM[2]
        train.initiative[laffey.id] = 100
        initiative_orgasm_proc(train, laffey, 2, 2)
        assert train.initiative[laffey.id] == 100 - int(100 * rate2)
        # 五重最强绝顶 lv4 num5：扣完且不为负
        train.initiative[laffey.id] = 80
        initiative_orgasm_proc(train, laffey, 4, 5)
        assert train.initiative[laffey.id] == 0


class TestGrowProc:
    """增长结算"""

    @staticmethod
    def _train(world):
        from game_engine.managers.TrainManager import Train
        return Train(world.player.location, world.player)

    def test_grow_suppressed_by_pleasure(self, world):
        train = self._train(world)
        laffey = world.npc_manager.shipgirls['laffey']
        z23 = world.npc_manager.shipgirls['Z23']
        base = INITIATIVE_BASE_GROWTH
        train.initiative = {world.player.id: 100, laffey.id: 0, z23.id: 0}
        # 玩家未受快感 +base；laffey 受半程快感；z23 受快感≥S_MAX → 不涨
        result = initiative_grow_proc(train, [
            (world.player, 0),
            (laffey, INITIATIVE_S_MAX // 2),
            (z23, INITIATIVE_S_MAX * 2),
        ])
        assert train.initiative[world.player.id] == 100 + base
        assert train.initiative[laffey.id] == int(base * 0.5)
        assert train.initiative[z23.id] == 0
        # 只有两个角色有增长消息
        assert len(result) == 2

    def test_grow_skips_non_participant(self, world):
        train = self._train(world)
        laffey = world.npc_manager.shipgirls['laffey']
        train.initiative = {world.player.id: 100}
        initiative_grow_proc(train, [(laffey, 0)])
        assert laffey.id not in train.initiative


class TestBatchHook:
    """source_proc_batch 挂接：每轮增长与绝顶衰减自动结算"""

    def _run(self, world, pairs):
        from game_engine.commands._common import source_proc_batch
        from game_engine.commands._context import CommandContext
        ctx = CommandContext(world)
        source_proc_batch(pairs, ctx)
        return ctx

    def _make_train(self, world):
        from game_engine.managers.TrainManager import Train
        train = Train(world.player.location, world.player)
        train.actors = ['player']
        train.targets = ['laffey']
        train.participants = ['player', 'laffey']
        train.initiative = {world.player.id: 100, 'laffey': 0}
        world.train_manager.train = train
        return train

    def test_round_growth_applied(self, world):
        from game_engine.commands._common import new_source
        train = self._make_train(world)
        laffey = world.npc_manager.shipgirls['laffey']
        base = INITIATIVE_BASE_GROWTH
        # 玩家给 laffey 少量快感：施与方 +base，受方被轻微压制
        src = new_source({'c_pleasure_source': 10})
        self._run(world, [(src.copy(), world.player, laffey)])
        assert train.initiative[world.player.id] == 100 + base
        assert train.initiative['laffey'] == int(base * (1 - 10 / INITIATIVE_S_MAX))

    def test_orgasm_triggers_initiative_decay(self, world):
        from game_engine.commands._common import new_source
        train = self._make_train(world)
        train.initiative = {world.player.id: 100, 'laffey': 100}
        laffey = world.npc_manager.shipgirls['laffey']
        # 直接堆 palam 触发 lv1 绝顶（15000），配合小快感指令
        laffey.palam['c_pleasure_palam'] = 14995
        src = new_source({'c_pleasure_source': 10})
        ctx = self._run(world, [(src.copy(), world.player, laffey)])
        # 绝顶衰减消息出现，主导权按配置衰减率结算后再吃本轮增长
        joined = '\n'.join(ctx.messages)
        assert '主导权-' in joined
        from config.initiative_config import ORGASM_INITIATIVE_RATE_LV, ORGASM_INITIATIVE_MULT_NUM
        decay = int(100 * ORGASM_INITIATIVE_RATE_LV[1] * ORGASM_INITIATIVE_MULT_NUM[1])
        expected = 100 - decay + int(INITIATIVE_BASE_GROWTH * (1 - 10 / INITIATIVE_S_MAX))
        assert train.initiative['laffey'] == expected
