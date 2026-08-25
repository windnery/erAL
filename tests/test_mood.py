from unittest.mock import patch

from config.mood_config import (
    MOOD_BAD, MOOD_NEUTRAL, MOOD_GOOD, MOOD_BLISS, MOOD_LABELS,
    MOOD_HALF_SATURATION, MOOD_MAX_PROB
)
from game_engine.commands._common import source_proc, source_proc_batch, new_source
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.mood.mood_calc import mood_proc, mood_natural_change, roll_daily_mood
from game_engine.models.shipgirl import ShipGirl
from world import World


class TestMoodModel:
    """测试 ShipGirl 心情基础属性与方法"""

    def test_default_mood(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        assert sg.get_mood() == MOOD_NEUTRAL
        assert sg.get_mood_label() == MOOD_LABELS[MOOD_NEUTRAL]

    def test_set_mood_and_clamping(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")

        # 正常设置
        sg.set_mood(MOOD_GOOD)
        assert sg.get_mood() == MOOD_GOOD
        assert sg.get_mood_label() == "好心情"

        sg.set_mood(MOOD_BLISS)
        assert sg.get_mood() == MOOD_BLISS
        assert sg.get_mood_label() == "幸福"

        sg.set_mood(MOOD_BAD)
        assert sg.get_mood() == MOOD_BAD
        assert sg.get_mood_label() == "愤怒"

        # 上限钳制 (MOOD_BLISS = 2)
        sg.set_mood(5)
        assert sg.get_mood() == MOOD_BLISS

        # 下限钳制 (MOOD_BAD = -1)
        sg.set_mood(-5)
        assert sg.get_mood() == MOOD_BAD

    def test_apply_mood_change(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_NEUTRAL)

        sg.apply_mood_change(1)
        assert sg.get_mood() == MOOD_GOOD

        sg.apply_mood_change(1)
        assert sg.get_mood() == MOOD_BLISS

        sg.apply_mood_change(1)  # 钳制在幸福
        assert sg.get_mood() == MOOD_BLISS

        sg.apply_mood_change(-3)
        assert sg.get_mood() == MOOD_BAD

    def test_mood_colors(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_BLISS)
        assert sg.get_mood_color() == '#ffd400'

        sg.set_mood(MOOD_GOOD)
        assert sg.get_mood_color() == '#66ccff'

        sg.set_mood(MOOD_BAD)
        assert sg.get_mood_color() == '#ff0000'

        sg.set_mood(MOOD_NEUTRAL)
        assert sg.get_mood_color() == ''

    def test_get_state_contains_mood(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_GOOD)
        state = sg.get_state()
        assert "mood" in state
        assert state["mood"] == MOOD_GOOD
        assert "mood_label" in state
        assert state["mood_label"] == "好心情"
        assert "mood_color" in state
        assert state["mood_color"] == "#66ccff"


class TestMoodProcCalculation:
    """测试 mood_proc 净 source 计算与概率映射"""

    def test_net_zero_does_not_change_mood(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_NEUTRAL)
        # 正负相等
        source = {"love_source": 1000, "disgust_source": 1000}
        mood_proc(source, sg)
        assert sg.get_mood() == MOOD_NEUTRAL

    def test_probability_calculation_and_capping(self):
        # 净值等于半饱和常数 (30000) 时，p = 100 * 30000 // 60000 = 50
        net = MOOD_HALF_SATURATION
        p_calc = 100 * net // (net + MOOD_HALF_SATURATION)
        assert p_calc == 50

        # 当 net 极大时，封顶于 MOOD_MAX_PROB (90)
        huge_net = 1_000_000
        p_huge = min(100 * huge_net // (huge_net + MOOD_HALF_SATURATION), MOOD_MAX_PROB)
        assert p_huge == MOOD_MAX_PROB

    def test_emotional_deficiency_talent_halves_prob(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_talent("emotional_deficiency", "1")
        assert sg.has_talent("emotional_deficiency")

        # 当净值为 30000，基础 p 为 50，感情缺乏后 p 变为 25
        # mock randint 返回 30：如果不减半 (50) 会成功，减半后 (25) 则失败
        source = {"love_source": 30000}
        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=30):
            mood_proc(source, sg)
            assert sg.get_mood() == MOOD_NEUTRAL  # 25 <= 30 不触发

        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=20):
            mood_proc(source, sg)
            assert sg.get_mood() == MOOD_GOOD  # 20 < 25 触发

    def test_mood_proc_positive_success(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_NEUTRAL)
        source = {"love_source": 10000}
        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=0):
            mood_proc(source, sg)
            assert sg.get_mood() == MOOD_GOOD

    def test_mood_proc_negative_success(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_NEUTRAL)
        source = {"disgust_source": 10000}
        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=0):
            mood_proc(source, sg)
            assert sg.get_mood() == MOOD_BAD

    def test_mood_proc_max_step_is_one(self):
        """单次指令最多变动 ±1"""
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_NEUTRAL)
        source = {"love_source": 100_000}
        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=0):
            mood_proc(source, sg)
            assert sg.get_mood() == MOOD_GOOD  # 从 0 变成 1，而不是直接满


class TestMoodNaturalChangeAndTimeDecay:
    """测试心情随时间向平静自然变化与日终重置"""

    def test_mood_natural_decay_good_to_neutral(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_BLISS)

        # 概率命中衰减
        with patch("game_engine.data_pipeline.mood.mood_calc.random", return_value=0.0):
            mood_natural_change(sg, dt=60)
            assert sg.get_mood() == MOOD_GOOD

            mood_natural_change(sg, dt=60)
            assert sg.get_mood() == MOOD_NEUTRAL

            # 已经平静则不再变化
            mood_natural_change(sg, dt=60)
            assert sg.get_mood() == MOOD_NEUTRAL

    def test_mood_natural_decay_bad_to_neutral(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_BAD)

        with patch("game_engine.data_pipeline.mood.mood_calc.random", return_value=0.0):
            mood_natural_change(sg, dt=60)
            assert sg.get_mood() == MOOD_NEUTRAL

    def test_shipgirl_mood_natural_change_method(self):
        sg = ShipGirl(id="test_sg", name="测试舰娘")
        sg.set_mood(MOOD_BAD)
        with patch("game_engine.data_pipeline.mood.mood_calc.random", return_value=0.0):
            sg.mood_natural_change(60)
            assert sg.get_mood() == MOOD_NEUTRAL

    def test_roll_daily_mood(self):
        for _ in range(50):
            m = roll_daily_mood()
            assert m in (MOOD_GOOD, MOOD_NEUTRAL, MOOD_BAD)

    def test_settle_day_resets_npc_mood(self):
        world = World()
        z23 = world.npc_manager.shipgirls["Z23"]
        z23.set_mood(MOOD_BAD)
        with patch("world.roll_daily_mood", return_value=MOOD_GOOD):
            world.settle_day(sleep=True)
            assert z23.get_mood() == MOOD_GOOD


class TestMoodPipelineAndCommands:
    """测试数据管线集成与指令门控/钩子"""

    def test_source_proc_triggers_mood_proc(self):
        world = World()
        z23 = world.npc_manager.shipgirls["Z23"]
        z23.set_mood(MOOD_NEUTRAL)
        ctx = CommandContext(world)
        source = new_source({"love_source": 50000})

        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=0):
            source_proc(source, world.player, z23, ctx)
            assert z23.get_mood() == MOOD_GOOD

    def test_source_proc_batch_triggers_mood_proc(self):
        world = World()
        z23 = world.npc_manager.shipgirls["Z23"]
        z23.set_mood(MOOD_NEUTRAL)
        ctx = CommandContext(world)
        source = new_source({"disgust_source": 50000})

        with patch("game_engine.data_pipeline.mood.mood_calc.randint", return_value=0):
            source_proc_batch([(source, world.player, z23)], ctx)
            assert z23.get_mood() == MOOD_BAD

    def test_push_down_can_gate_when_angry(self):
        from game_engine.commands.interact.push_down import can
        world = World()
        z23 = world.npc_manager.shipgirls["Z23"]
        z23.favor = 1000
        z23.abl["intimacy_abl"] = 10
        z23.set_talent("relationship", "2")
        z23.set_mood(MOOD_NEUTRAL)

        assert can(world, z23) is True

        # 愤怒状态下不可推倒
        z23.set_mood(MOOD_BAD)
        assert can(world, z23) is False

    def test_push_down_failure_sets_bad_mood(self):
        from game_engine.commands.interact.push_down import push_down
        world = World()
        z23 = world.npc_manager.shipgirls["Z23"]
        z23.favor = 1000
        z23.abl["intimacy_abl"] = 10
        z23.set_talent("relationship", "2")
        z23.set_mood(MOOD_NEUTRAL)

        # mock able 返回失败
        with patch("game_engine.commands.interact.push_down.able", return_value=(False, "测试失败")):
            push_down(world, "Z23")
            assert z23.get_mood() == MOOD_BAD
