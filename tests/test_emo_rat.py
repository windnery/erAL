# -*- coding: utf-8 -*-
"""情绪/理性（emotion/rationality）系统测试

覆盖四层：
1. emo_rat_calc：source → 情绪/理性 计算（权重分类、//1000 截断、clamp）
2. emo_rat2src：情绪/理性 → source 反作用（4 档位边界）
3. emo_rat2favor / emo_rat2trust：情绪/理性 → 好感/信赖 修正
4. shipgirl 状态方法：set/get/clamp、自然变动、重置
5. common_src_modify 集成：emo_rat2src 真的被整链调用

注意：这些测试期望的是「当前代码的实际行为」。
如果某些行为与设计意图不符，请报告用户，由用户决定是否改代码。
"""
from config.base_config import MAX_EMOTION, MAX_RATIONALITY, MIN_EMOTION
from config.source_config import (
    ALL_SOURCE_KEYS, EMOTION_POS_SRC1, EMOTION_POS_SRC2, EMOTION_NEG_SRC1, EMOTION_NEG_SRC2,
    RATIONALITY_POS_SRC, RATIONALITY_NEG_SRC,
)


def _src(**overrides):
    """构造全 0 source 字典，可覆盖指定键"""
    d = {k: 0 for k in ALL_SOURCE_KEYS}
    d.update(overrides)
    return d


# ============================================================
# 第一层：emo_rat_calc（source → 情绪/理性）
# ============================================================
class TestEmotionRationalityCalc:
    def test_pos_src1_raises_emotion(self, z23):
        """情绪正向1（weight=15）：love_source=1000 → e_score=15000//1000=15"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(0)
        emotion_rationality_calc(_src(love_source=1000), z23)
        assert z23.get_emotion() == 15

    def test_pos_src2_raises_emotion(self, z23):
        """情绪正向2（weight=10）：happiness_source=1000 → +10"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(0)
        emotion_rationality_calc(_src(happiness_source=1000), z23)
        assert z23.get_emotion() == 10

    def test_neg_src1_lowers_emotion(self, z23):
        """情绪负向1（weight=12）：pain_source=1000 → -12"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(100)
        emotion_rationality_calc(_src(pain_source=1000), z23)
        assert z23.get_emotion() == 88

    def test_neg_src2_lowers_emotion(self, z23):
        """情绪负向2（weight=8）：escape_source=1000 → -8"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(100)
        emotion_rationality_calc(_src(escape_source=1000), z23)
        assert z23.get_emotion() == 92

    def test_neg_src_lowers_rationality(self, z23):
        """理性负向（weight=12）：love_source=1000 → r_score=-12000//1000=-12"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_rationality(1000)
        emotion_rationality_calc(_src(love_source=1000), z23)
        assert z23.get_rationality() == 988

    def test_pos_src_raises_rationality(self, z23):
        """理性正向（weight=8）：pain_source=1000 → +8"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_rationality(500)
        emotion_rationality_calc(_src(pain_source=1000), z23)
        assert z23.get_rationality() == 508

    def test_mixed_sources_accumulate(self, z23):
        """混合多 source：love(15) + happiness(10) - pain(12) = +13"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(0)
        emotion_rationality_calc(_src(love_source=1000, happiness_source=1000, pain_source=1000), z23)
        assert z23.get_emotion() == 13

    def test_floor_division_truncates(self, z23):
        """//1000 截断：love_source=500 → 7500//1000=7（不是 7.5 也不是 8）"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(0)
        emotion_rationality_calc(_src(love_source=500), z23)
        assert z23.get_emotion() == 7

    def test_negative_floor_division_truncates(self, z23):
        """负向 //1000 截断：pain_source=500 → -6000//1000=-6（Python 向下取整）"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(100)
        emotion_rationality_calc(_src(pain_source=500), z23)
        assert z23.get_emotion() == 94  # 100 - 6

    def test_emotion_clamped_at_max(self, z23):
        """情绪 clamp：990 + 20 → 封顶 1000"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(990)
        # love_source=1000 weight15 → +15；再乘多键无意义，直接验证封顶
        emotion_rationality_calc(_src(love_source=1000), z23)
        assert z23.get_emotion() == 1000

    def test_emotion_clamped_at_min(self, z23):
        """情绪 clamp：10 - 20 → 归 0"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_emotion(10)
        emotion_rationality_calc(_src(pain_source=2000), z23)  # -24000//1000=-24
        assert z23.get_emotion() == 0

    def test_rationality_clamped_at_min(self, z23):
        """理性 clamp：10 - 20 → 归 0"""
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        z23.set_rationality(10)
        emotion_rationality_calc(_src(love_source=2000), z23)  # -24000//1000=-24
        assert z23.get_rationality() == 0

    def test_all_sources_classified(self):
        """分类覆盖完备性：
        - 情绪分类：除 4 个中性源（lubrication/passivity/exposure/sex_act）外全部覆盖
        - 理性分类：除 4 个中性源 + 3 个理性中性源（escape/unclean/depression，不影响理性）外全部覆盖
        （若新增 source 键漏分类，此测试会亮红提醒补分类）"""
        all_keys = set(ALL_SOURCE_KEYS)
        neutral = {'lubrication_source', 'passivity_source', 'exposure_source', 'sex_act_source'}
        rat_neutral = neutral | {'escape_source', 'unclean_source', 'depression_source'}
        emo_covered = EMOTION_POS_SRC1 | EMOTION_POS_SRC2 | EMOTION_NEG_SRC1 | EMOTION_NEG_SRC2
        rat_covered = RATIONALITY_POS_SRC | RATIONALITY_NEG_SRC
        assert emo_covered == all_keys - neutral, f"情绪分类异常: 多={emo_covered - (all_keys - neutral)} 漏={all_keys - neutral - emo_covered}"
        assert rat_covered == all_keys - rat_neutral, f"理性分类异常: 多={rat_covered - (all_keys - rat_neutral)} 漏={all_keys - rat_neutral - rat_covered}"


# ============================================================
# 第二层：emo_rat2src（情绪/理性 → source 反作用）
# ============================================================
class TestEmoRat2Src:
    def test_emotion_below_100_no_modifier(self, z23):
        """情绪 <100 无修正（×1.0）"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(99)
        z23.set_rationality(1000)  # 理性 >900 无修正
        src = _src(love_source=1000, pain_source=1000)
        emo_rat2src(z23, src)
        assert src['love_source'] == 1000
        assert src['pain_source'] == 1000

    def test_emotion_100_tier(self, z23):
        """情绪 100 档：正向 ×1.25、负向 ×0.9"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(100)
        z23.set_rationality(1000)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 125
        assert src['pain_source'] == 90

    def test_emotion_250_tier(self, z23):
        """情绪 250 档：正向 ×1.5、负向 ×0.75"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(250)
        z23.set_rationality(1000)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 150
        assert src['pain_source'] == 75

    def test_emotion_500_tier(self, z23):
        """情绪 500 档：正向 ×1.75、负向 ×0.6"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(500)
        z23.set_rationality(1000)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 175
        assert src['pain_source'] == 60

    def test_emotion_750_tier(self, z23):
        """情绪 750 档：正向 ×2.0、负向 ×0.5"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(750)
        z23.set_rationality(1000)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 200
        assert src['pain_source'] == 50

    def test_rationality_low_tier(self, z23):
        """理性 0~249 档：正向 ×2.0、负向 ×0.5"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(0)
        z23.set_rationality(249)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 200
        assert src['pain_source'] == 50

    def test_rationality_250_tier(self, z23):
        """理性 250 档：正向 ×1.75、负向 ×0.6"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(0)
        z23.set_rationality(250)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 175
        assert src['pain_source'] == 60

    def test_rationality_500_tier(self, z23):
        """理性 500 档：正向 ×1.5、负向 ×0.75"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(0)
        z23.set_rationality(500)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 150
        assert src['pain_source'] == 75

    def test_rationality_750_tier(self, z23):
        """理性 750 档：正向 ×1.25、负向 ×0.9"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(0)
        z23.set_rationality(750)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 125
        assert src['pain_source'] == 90

    def test_rationality_above_900_no_modifier(self, z23):
        """理性 >900 无修正（×1.0）"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(0)
        z23.set_rationality(901)
        src = _src(love_source=100, pain_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 100
        assert src['pain_source'] == 100

    def test_emotion_and_rationality_multiply(self, z23):
        """情绪×理性 权重相乘：emo=750(2.0) × rat=0(2.0) → 正向 ×4"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(750)
        z23.set_rationality(0)
        src = _src(love_source=100)
        emo_rat2src(z23, src)
        assert src['love_source'] == 400

    def test_positive_negative_independent(self, z23):
        """正负 source 独立修正：同时存在互不干扰"""
        from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
        z23.set_emotion(750)
        z23.set_rationality(1000)
        src = _src(love_source=200, pain_source=200, escape_source=200)
        emo_rat2src(z23, src)
        assert src['love_source'] == 400   # 200 × 2.0
        assert src['pain_source'] == 100   # 200 × 0.5
        assert src['escape_source'] == 100  # 200 × 0.5（负向统一 ×0.5）


# ============================================================
# 第三层：emo_rat2favor / emo_rat2trust
# ============================================================
class TestEmoRat2Favor:
    def test_emotion_200_tier(self):
        """情绪 200~499 → +1"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(200, 1000) == 1
        assert emo_rat2favor(499, 1000) == 1

    def test_emotion_500_tier(self):
        """情绪 500~799 → +2"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(500, 1000) == 2
        assert emo_rat2favor(799, 1000) == 2

    def test_emotion_800_tier(self):
        """情绪 ≥800 → +3"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(800, 1000) == 3
        assert emo_rat2favor(1000, 1000) == 3

    def test_rationality_below_500(self):
        """理性 <500 → +2"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(0, 499) == 2

    def test_rationality_500_800(self):
        """理性 500~799 → +1"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(0, 500) == 1
        assert emo_rat2favor(0, 799) == 1

    def test_rationality_above_800_no_bonus(self):
        """理性 ≥800 → +0"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(0, 800) == 0
        assert emo_rat2favor(0, 1000) == 0

    def test_combined(self):
        """组合：emotion=800(+3) + rationality=200(+2) = +5"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(800, 200) == 5

    def test_no_effect_when_low_emotion_high_rationality(self):
        """情绪 0 且理性 1000 → +0"""
        from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
        assert emo_rat2favor(0, 1000) == 0


class TestEmoRat2Trust:
    def test_same_tiers_as_favor(self):
        """信赖与好感同构（当前实现）：emotion=800(+3) + rationality=200(+2) = +5"""
        from game_engine.data_pipeline.base.emo_rat2trust import emo_rat2trust
        assert emo_rat2trust(800, 200) == 5
        assert emo_rat2trust(200, 1000) == 1
        assert emo_rat2trust(0, 1000) == 0


# ============================================================
# 第四层：shipgirl 状态方法
# ============================================================
class TestShipGirlEmotionRationality:
    def test_get_default_emotion(self, z23):
        """默认情绪 = MIN_EMOTION(0)（base 缺省时兜底）"""
        z23.base.pop('emotion', None)
        assert z23.get_emotion() == MIN_EMOTION

    def test_get_default_rationality(self, z23):
        """默认理性 = MAX_RATIONALITY(1000)（base 缺省时兜底）"""
        z23.base.pop('rationality', None)
        assert z23.get_rationality() == MAX_RATIONALITY

    def test_set_emotion_clamps_low(self, z23):
        """set_emotion 负数 → 0"""
        z23.set_emotion(-50)
        assert z23.get_emotion() == 0

    def test_set_emotion_clamps_high(self, z23):
        """set_emotion 超上限 → 1000"""
        z23.set_emotion(1500)
        assert z23.get_emotion() == MAX_EMOTION

    def test_set_rationality_clamps_low(self, z23):
        """set_rationality 负数 → 0"""
        z23.set_rationality(-50)
        assert z23.get_rationality() == 0

    def test_set_rationality_clamps_high(self, z23):
        """set_rationality 超上限 → 1000"""
        z23.set_rationality(1500)
        assert z23.get_rationality() == MAX_RATIONALITY

    def test_emotion_natural_change_decays(self, z23):
        """情绪自然衰减：emotion=1000, dt=60 → 1000 - 60*4*1500//500 = 1000-720 = 280"""
        z23.set_emotion(1000)
        z23.emotion_natural_change(60)
        assert z23.get_emotion() == 280

    def test_emotion_natural_change_clamped_at_zero(self, z23):
        """情绪自然衰减不跌穿 0：emotion=100, dt=60 → 100-720 → 0"""
        z23.set_emotion(100)
        z23.emotion_natural_change(60)
        assert z23.get_emotion() == 0

    def test_rationality_natural_change_recovers(self, z23):
        """理性自然恢复：rationality=0, dt=60 → 0 + 60*1500//500 = 180"""
        z23.set_rationality(0)
        z23.rationality_natural_change(60)
        assert z23.get_rationality() == 180

    def test_rationality_natural_change_faster_when_low(self, z23):
        """理性越低恢复越快：dt=60 时 rat=0 涨 180 > rat=500 涨 90"""
        z23.set_rationality(0)
        z23.rationality_natural_change(60)
        low = z23.get_rationality()
        z23.set_rationality(500)
        z23.rationality_natural_change(60)
        high = z23.get_rationality() - 500
        assert low > high

    def test_rationality_natural_change_clamped_at_max(self, z23):
        """理性自然恢复不超上限：rationality=1000, dt=60 → 1000+60 → 1000"""
        z23.set_rationality(1000)
        z23.rationality_natural_change(60)
        assert z23.get_rationality() == 1000

    def test_reset_emotion(self, z23):
        """reset_emotion → 0"""
        z23.set_emotion(500)
        z23.reset_emotion()
        assert z23.get_emotion() == MIN_EMOTION

    def test_reset_rationality(self, z23):
        """reset_rationality → 1000"""
        z23.set_rationality(0)
        z23.reset_rationality()
        assert z23.get_rationality() == MAX_RATIONALITY


# ============================================================
# 第五层：common_src_modify 集成（emo_rat2src 整链生效）
# ============================================================
class TestCommonSrcModifyEmoRat:
    def test_baseline_no_emotion_modifier(self, world, z23_nearby, source_dict):
        """基线：emotion=0(默认) + rationality=1000(默认) → 无情绪修正，love=1040"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        z23_nearby.set_emotion(0)
        z23_nearby.set_rationality(1000)
        src = dict(source_dict)
        src['love_source'] = 1000
        z23_nearby.favor = 300
        z23_nearby.talent = {'relationship': '0'}
        z23_nearby.abl = {k: 0 for k in z23_nearby.abl}
        # Z23 默认 relationship=0（陌生 ×0.8）
        result = common_src_modify(src, z23_nearby)
        assert result['love_source'] == 1040  # 1000*1.3*0.8

    def test_high_emotion_doubles_positive(self, world, z23_nearby, source_dict):
        """emotion=800 → 正向 ×2.0：1040 → 2080"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        z23_nearby.set_emotion(800)
        z23_nearby.set_rationality(1000)
        src = dict(source_dict)
        src['love_source'] = 1000
        z23_nearby.favor = 300
        z23_nearby.talent = {'relationship': '0'}
        z23_nearby.abl = {k: 0 for k in z23_nearby.abl}
        result = common_src_modify(src, z23_nearby)
        assert result['love_source'] == 2080  # 1040*2.0

    def test_high_emotion_halves_negative(self, world, z23_nearby, source_dict):
        """emotion=800 → 负向 ×0.5：pain 基线 → 0.5（int 截断）"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        z23_nearby.set_emotion(0)
        z23_nearby.set_rationality(1000)
        src = dict(source_dict)
        src['pain_source'] = 1000
        z23_nearby.favor = 300
        z23_nearby.talent = {'relationship': '0'}
        z23_nearby.abl = {k: 0 for k in z23_nearby.abl}
        baseline = common_src_modify(dict(src), z23_nearby)['pain_source']
        # emotion=800 → 负向 ×0.5
        z23_nearby.set_emotion(800)
        result = common_src_modify(src, z23_nearby)
        assert result['pain_source'] == int(baseline * 0.5)

    def test_low_rationality_doubles_positive(self, world, z23_nearby, source_dict):
        """rationality=0 → 正向 ×2.0：1040 → 2080"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        z23_nearby.set_emotion(0)
        z23_nearby.set_rationality(0)
        src = dict(source_dict)
        src['love_source'] = 1000
        z23_nearby.favor = 300
        z23_nearby.talent = {'relationship': '0'}
        z23_nearby.abl = {k: 0 for k in z23_nearby.abl}
        result = common_src_modify(src, z23_nearby)
        assert result['love_source'] == 2080  # 1040*2.0


# ============================================================
# 第六层：source 类型约定（约定C）
# 全链路允许 int|float，common_src_modify 出口统一转 int，
# 防止 float 泄漏进 emotion/rationality 存档值。
# ============================================================
class TestSourceTypeInvariant:
    def test_common_src_modify_returns_int_values(self, world, z23_nearby, source_dict):
        """约定C：common_src_modify 出口必须全部转回 int"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        src = dict(source_dict)
        src['pain_source'] = 15
        src['v_pleasure_source'] = 120
        z23_nearby.favor = 300
        result = common_src_modify(src, z23_nearby)
        assert all(isinstance(v, int) for v in result.values())

    def test_float_source_no_emotion_leak(self, world, z23_nearby, source_dict):
        """float source（pain_check_v 前置）流入 emotion_rationality_calc 后，情绪/理性保持 int"""
        from game_engine.commands._common import pain_check_v
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
        src = dict(source_dict)
        src['pain_source'] = 15
        src['v_pleasure_source'] = 120
        # 模拟 finger_insert 修复后的顺序：pain_check_v 在 common_src_modify 之前
        pain_check_v(src, z23_nearby)
        assert not all(isinstance(v, int) for v in src.values())
        src = common_src_modify(src, z23_nearby)
        assert all(isinstance(v, int) for v in src.values())
        emotion_rationality_calc(src, z23_nearby)
        assert isinstance(z23_nearby.get_emotion(), int)
        assert isinstance(z23_nearby.get_rationality(), int)
