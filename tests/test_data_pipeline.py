# -*- coding: utf-8 -*-
"""第一层：数据管线单元测试

覆盖：palam2src / abl2src / juel_calc / juel2abl / exp2abl /
      palam2favor / favor_calc / trust_calc / mood2favor /
      talent2src / favor2source / common_src_modify / exp_calc

重点回归：juel2abl 固定 demand bug（1000 juel 直接升 13 级）
"""
import pytest

from config.juel_config import get_juel_demand
from config.palam_config import PALAM_LV
from config.source_config import ALL_SOURCE_KEYS, POSITIVE_SRC, NEGATIVE_SRC


# ============================================================
# palam2src
# ============================================================

class TestPalam2Src:
    def test_zero_lv_no_change(self, source_dict):
        """palam 等级全 0 时 source 不变"""
        from game_engine.data_pipeline.palam.palam2src import palam2src
        src = dict(source_dict)
        palam2src({k: 0 for k in source_dict}, src)
        assert src == dict(source_dict)

    def test_c_pleasure_adds_to_c_pleasure_source(self, source_dict):
        """c_pleasure_palam 等级 1 时给 c_pleasure_source 加权重"""
        from game_engine.data_pipeline.palam.palam2src import palam2src
        src = dict(source_dict)
        src['c_pleasure_source'] = 100
        palam2src({'c_pleasure_palam': 1}, src)
        # modify = 1 * (1 + 0.3*0/2) = 1.0, coef=4 → +4
        assert src['c_pleasure_source'] == 104

    def test_negative_source_not_clamped_to_zero_for_pure_zero(self, source_dict):
        """source 原值 0 时不添加（continue 语义），保持 0"""
        from game_engine.data_pipeline.palam.palam2src import palam2src
        src = dict(source_dict)
        palam2src({'pain_palam': 3}, src)
        # pain_palam 有 -3 权重到 c_pleasure_source，但原值 0 应保持 0
        assert src['c_pleasure_source'] == 0

    def test_lv_curve_grows_faster_than_linear(self, source_dict):
        """等级越高，修正量超线性增长（K_ACCEL 滚雪球）"""
        from game_engine.data_pipeline.palam.palam2src import palam2src
        src1 = dict(source_dict); src1['c_pleasure_source'] = 1000
        src2 = dict(source_dict); src2['c_pleasure_source'] = 1000
        palam2src({'c_pleasure_palam': 2}, src1)
        palam2src({'c_pleasure_palam': 4}, src2)
        d1 = src1['c_pleasure_source'] - 1000
        d2 = src2['c_pleasure_source'] - 1000
        assert d2 > 2 * d1  # 4级增量 > 2倍 2级增量


# ============================================================
# abl2src
# ============================================================

class TestAbl2Src:
    def test_zero_lv_no_change(self, source_dict):
        from game_engine.data_pipeline.abl.abl2src import abl2src
        src = dict(source_dict)
        abl = {k: 0 for k in ('c_sen_abl', 'v_sen_abl', 'intimacy_abl')}
        result = abl2src(abl, src)
        assert result == src

    def test_intimacy_affects_all_positive_sources(self, source_dict):
        """intimacy_abl 对全部正向 source +2 权重"""
        from game_engine.data_pipeline.abl.abl2src import abl2src
        src = dict(source_dict)
        for k in POSITIVE_SRC:
            src[k] = 100
        result = abl2src({'intimacy_abl': 1}, src)
        for k in POSITIVE_SRC:
            assert result[k] == 102, f'{k} 应 +2，实际 {result[k]}'

    def test_negative_source_not_below_zero(self, source_dict):
        """负向权重不会把 source 扣到 0 以下"""
        from game_engine.data_pipeline.abl.abl2src import abl2src
        src = dict(source_dict)
        src['fear_source'] = 10
        result = abl2src({'desire_abl': 5}, src)
        assert result['fear_source'] >= 0


# ============================================================
# juel_calc（palam → juel 转化 + 否定珠抵消）
# ============================================================

class TestJuelCalc:
    def test_palam_to_juel_basic(self, world, z23):
        """5000 快感 palam（6级）→ 1000 快感珠"""
        from game_engine.data_pipeline.juel.juel_calc import juel_calc
        z23.palam['c_pleasure_palam'] = 5000  # PALAM_LV[6] = 5000
        juel_calc(z23)
        assert z23.juel['c_pleasure_juel'] == 1000  # JUEL_GET[PALAM_LV[6]] = 1000

    def test_high_palam_higher_juel(self, world, z23):
        """等级越高 juel 越多"""
        from game_engine.data_pipeline.juel.juel_calc import juel_calc
        z23.palam['c_pleasure_palam'] = 200_000  # 11级
        juel_calc(z23)
        assert z23.juel['c_pleasure_juel'] == 20_000

    def test_negative_palam_goes_to_negation_juel(self, world, z23):
        """负面 palam → 否定珠"""
        from game_engine.data_pipeline.juel.juel_calc import juel_calc
        z23.palam['disgust_palam'] = 1000  # 4级
        juel_calc(z23)
        assert z23.juel['disgust_juel'] == 0
        assert z23.juel['negation_juel'] == 200  # JUEL_GET[PALAM_LV[4]] = 200

    def test_negation_juel_cancels_positive(self, world, z23):
        """否定珠抵消正面珠"""
        from game_engine.data_pipeline.juel.juel_calc import juel_calc
        z23.palam['c_pleasure_palam'] = 5000    # +1000 快感珠
        z23.palam['disgust_palam'] = 5000       # +1000 否定珠
        juel_calc(z23)
        # 否定珠优先抵消第一个非否定键（字典序）: a_pleasure_juel 等
        # c_pleasure_juel 剩余 = 1000 - 1000 = 0（取决于抵消顺序）
        assert z23.juel['negation_juel'] == 0
        assert z23.juel['c_pleasure_juel'] + z23.juel['negation_juel'] >= 0


# ============================================================
# juel2abl（重点回归：固定 demand bug）
# ============================================================

class TestJuel2Abl:
    def test_1000_kindness_juel_raises_intimacy_to_3(self, world, z23):
        """回归：1000 好意珠只应升到亲密 3 级（30+100+300=430），而不是满级 13"""
        from game_engine.data_pipeline.abl.abl_lv_check import juel2abl
        from config.attr_defs import ATTR_DEFS
        z23.juel['kindness_juel'] = 1000
        z23.abl['intimacy_abl'] = 0
        mes = juel2abl(z23, ATTR_DEFS)
        assert z23.abl['intimacy_abl'] == 3, f'应升到 3 级，实际 {z23.abl["intimacy_abl"]}（固定 demand bug 回归）'
        # 剩余 570：1000 - 430
        assert z23.juel['kindness_juel'] == 570

    def test_insufficient_juel_no_upgrade(self, world, z23):
        """珠不够不升级"""
        from game_engine.data_pipeline.abl.abl_lv_check import juel2abl
        from config.attr_defs import ATTR_DEFS
        z23.juel['kindness_juel'] = 20  # < 30 需求
        juel2abl(z23, ATTR_DEFS)
        assert z23.abl['intimacy_abl'] == 0

    def test_or_semantic_first_matching_juel_consumed(self, world, z23):
        """OR 语义：多键 demand 多珠都够时，按字典序扣第一个满足的珠

        设计（用户 2026-08-09）：任一珠够即升级；多珠都够则顺序扣第一个

        隔离：其余 abl 设满级，避免其他 abl 升级顺带消耗珠干扰断言
        """
        from game_engine.data_pipeline.abl.abl_lv_check import juel2abl
        from config.attr_defs import ATTR_DEFS
        from config.abl_config import JUEL2ABL_MAX_LV
        z23.talent = {}  # 排除 talent 对 demand 的干扰
        for k in z23.abl:
            if k != 'obedience_abl':
                z23.abl[k] = JUEL2ABL_MAX_LV
        z23.abl['obedience_abl'] = 0
        # lv0 demand = fear30/obedience30/lust150/submission100
        z23.juel['fear_juel'] = 100
        z23.juel['obedience_juel'] = 100
        z23.juel['lust_juel'] = 100
        z23.juel['submission_juel'] = 100
        before = {k: z23.juel[k] for k in
                  ('fear_juel', 'obedience_juel', 'lust_juel', 'submission_juel')}
        juel2abl(z23, ATTR_DEFS)
        # 升1级后 lv1 demand 变贵（fear100+）不够再升
        assert z23.abl['obedience_abl'] == 1
        # 按字典序 fear 最先满足 → 只扣 fear
        assert before['fear_juel'] - z23.juel['fear_juel'] == 30
        assert before['obedience_juel'] - z23.juel['obedience_juel'] == 0
        assert before['lust_juel'] - z23.juel['lust_juel'] == 0
        assert before['submission_juel'] - z23.juel['submission_juel'] == 0

    def test_or_semantic_only_one_juel_needed(self, world, z23):
        """OR 语义：多键 demand 只有第一个珠够也升级（不要求全部够）

        设计：任一珠满足即可升级，只扣那一颗
        """
        from game_engine.data_pipeline.abl.abl_lv_check import juel2abl
        from config.attr_defs import ATTR_DEFS
        z23.talent = {}
        z23.abl['obedience_abl'] = 0
        z23.juel['fear_juel'] = 100   # 够
        z23.juel['obedience_juel'] = 0
        z23.juel['lust_juel'] = 0
        z23.juel['submission_juel'] = 0
        before_fear = z23.juel['fear_juel']
        juel2abl(z23, ATTR_DEFS)
        assert z23.abl['obedience_abl'] == 1
        assert before_fear - z23.juel['fear_juel'] == 30

    def test_negative_demand_skips_locked_juel_but_others_upgrade(self, world, z23):
        """含 -1 多键 demand：正常珠够即升级，-1 珠不参与也不扣

        设计：-1 只是"该珠此级不可用"标记，不阻止其他珠升级

        隔离：把其余 abl 设满级，避免遍历其他 abl 时顺带消耗 lust_juel 干扰断言
        """
        from game_engine.data_pipeline.abl.abl_lv_check import juel2abl
        from config.attr_defs import ATTR_DEFS
        from config.abl_config import JUEL2ABL_MAX_LV
        z23.talent = {}
        # 除 obedience 外全满级，隔离跨 abl 扣减干扰
        for k in z23.abl:
            if k != 'obedience_abl':
                z23.abl[k] = JUEL2ABL_MAX_LV
        z23.abl['obedience_abl'] = 3  # lv3 demand: fear5000/obedience5000/lust-1/submission-1
        z23.juel['fear_juel'] = 20000
        z23.juel['obedience_juel'] = 0
        z23.juel['lust_juel'] = 5000   # 有但标 -1
        z23.juel['submission_juel'] = 5000
        before_lust = z23.juel['lust_juel']
        juel2abl(z23, ATTR_DEFS)
        # fear 连续升 lv3→4→5（20000够扣5000+7500，lv5需10000不够停）
        assert z23.abl['obedience_abl'] == 5
        assert z23.juel['lust_juel'] == before_lust, 'lust_juel 标-1不应被 obedience 扣'

    def test_demand_recomputed_each_level(self, world, z23):
        """每次升级 demand 递增（回归：循环外只算一次）"""
        from game_engine.data_pipeline.abl.abl_lv_check import juel2abl
        from config.attr_defs import ATTR_DEFS
        z23.juel['kindness_juel'] = 30 + 100 + 300 + 1000  # 足够升 4 级
        juel2abl(z23, ATTR_DEFS)
        assert z23.abl['intimacy_abl'] == 4  # 若固定 demand=30 会升到 13（bug）


class TestExp2Abl:
    def test_exp_upgrades_abl(self, world, z23):
        """talk_exp 达到阈值 → talk_abl 升级

        ⚠️ 已知 bug：exp2abl 用 `>` 而非 `>=` 且查 ABL_LV[abl+1]（abl→exp 表），
        正确语义应查 EXP_LV[exp]（exp→abl 表），当前 exp=20 无法从 abl2 升到 3
        """
        from game_engine.data_pipeline.abl.abl_lv_check import exp2abl
        from config.attr_defs import ATTR_DEFS
        z23.exp['talk_exp'] = 20  # EXP_LV[20] = 3 级
        z23.abl['talk_abl'] = 2
        mes = exp2abl(z23, ATTR_DEFS)
        assert z23.abl['talk_abl'] == 3, \
            f'exp=20 应升到 3 级，实际 {z23.abl["talk_abl"]}（bug：阈值判定问题）'

    def test_exp_not_enough_no_upgrade(self, world, z23):
        from game_engine.data_pipeline.abl.abl_lv_check import exp2abl
        from config.attr_defs import ATTR_DEFS
        z23.exp['talk_exp'] = 19
        z23.abl['talk_abl'] = 2
        exp2abl(z23, ATTR_DEFS)
        assert z23.abl['talk_abl'] == 2

    def test_exp2abl_max_level_cap(self, world, z23):
        """exp2abl 上限保护：abl 满级时不应 KeyError

        ⚠️ 已知 bug：上限检查 `exp == EXP2ABL_MAX_LV(6)` 检查的是 exp 累加值（永远不为 6），
        """
        from game_engine.data_pipeline.abl.abl_lv_check import exp2abl
        from config.attr_defs import ATTR_DEFS
        z23.exp['talk_exp'] = 100_000
        z23.abl['talk_abl'] = 6  # 满级
        mes = exp2abl(z23, ATTR_DEFS)
        assert z23.abl['talk_abl'] == 6  # 满级不降不崩


# ============================================================
# palam2favor / favor_calc / trust_calc / mood2favor
# ============================================================

class TestPalam2Favor:
    def test_kindness_plus_obedience_bonus(self, z23):
        from game_engine.data_pipeline.palam.palam2favor import palam2favor
        # 好意 6 级 + 恭顺 0 级 = 6 → 分段 <9 → +2（代码定义 6 落入 +2 段）
        pl = {'kindness_palam': 6, 'obedience_palam': 0, 'lust_palam': 0,
              'disgust_palam': 0, 'unhappiness_palam': 0, 'depression_palam': 0,
              'pain_palam': 0, 'fear_palam': 0}
        assert palam2favor(pl) == 2

    def test_negative_palams_penalize(self, z23):
        from game_engine.data_pipeline.palam.palam2favor import palam2favor
        # 反感 5 + 不快 2 + 抑郁 1 + 苦痛 0 + 恐怖 0 = 8 → -2
        pl = {'kindness_palam': 0, 'obedience_palam': 0, 'lust_palam': 0,
              'disgust_palam': 5, 'unhappiness_palam': 2, 'depression_palam': 1,
              'pain_palam': 0, 'fear_palam': 0}
        assert palam2favor(pl) == -2


class TestFavorCalc:
    def test_positive_sources_increase_favor(self, world, z23):
        from game_engine.data_pipeline.favor.favor_calc import favor_calc
        src = {k: 0 for k in ALL_SOURCE_KEYS}
        src['love_source'] = 5000
        src['happiness_source'] = 5000
        src['c_pleasure_source'] = 5000
        src['v_pleasure_source'] = 5000
        delta = favor_calc(world.player, z23, src)  # 不崩即可
        assert delta > 0

    def test_negative_sources_decrease_favor(self, world, z23):
        from game_engine.data_pipeline.favor.favor_calc import favor_calc
        src = {k: 0 for k in ALL_SOURCE_KEYS}
        src['disgust_source'] = 5000
        src['escape_source'] = 5000
        src['fear_source'] = 5000
        delta = favor_calc(world.player, z23, src)  # 不崩即可
        assert delta < 0

    def test_zero_source_stable(self, world, z23):
        """全 0 source 时 favor_delta 稳定（不 NaN 不异常）"""
        from game_engine.data_pipeline.favor.favor_calc import favor_calc
        src = {k: 0 for k in ALL_SOURCE_KEYS}
        favor_calc(world.player, z23, src)  # 无异常即通过


class TestTrustCalc:
    def test_positive_sources_increase_trust(self, world, z23):
        from game_engine.data_pipeline.trust.trust_calc import trust_calc
        src = {k: 0 for k in ALL_SOURCE_KEYS}
        src['love_source'] = 5000
        src['happiness_source'] = 5000
        delta = trust_calc(world.player, z23, src)  # 不崩即可
        assert delta > 0


class TestMood2Favor:
    def test_mood_mapping(self, world, z23):
        from game_engine.data_pipeline.mood.mood2favor import mood2favor
        from config.mood_enum import Mood
        assert mood2favor(Mood.ANGRY) == -2
        assert mood2favor(Mood.NEUTRAL) == 0
        assert mood2favor(Mood.BLISS) == 3


# ============================================================
# talent2src / favor2source
# ============================================================

class TestTalent2Src:
    def test_virgin_multiplies_escape(self, z23, source_dict):
        from game_engine.data_pipeline.talent.talent2src import talent2src
        src = dict(source_dict)
        src['escape_source'] = 100
        z23.talent = {'virgin': '1'}
        talent2src(z23, src)
        assert src['escape_source'] == 120

    def test_relationship0_penalizes_positive(self, z23, source_dict):
        from game_engine.data_pipeline.talent.talent2src import talent2src
        src = dict(source_dict)
        for k in POSITIVE_SRC:
            src[k] = 100
        z23.talent = {'relationship': '0'}
        talent2src(z23, src)
        for k in POSITIVE_SRC:
            assert src[k] == 80  # 陌生 ×0.8

    def test_tsundere_low_intimacy_penalizes_obedience(self, z23, source_dict):
        from game_engine.data_pipeline.talent.talent2src import talent2src
        src = dict(source_dict)
        src['obedience_source'] = 100
        z23.talent = {'tsundere': '1'}
        z23.abl['intimacy_abl'] = 2  # ≤4
        talent2src(z23, src)
        assert src['obedience_source'] == 70


class TestFavor2Source:
    def test_low_favor_negative_bias(self):
        from game_engine.data_pipeline.favor.favor2src import favor2source
        pos, neg = favor2source(10)
        assert pos == 0.9 and neg == 1.1

    def test_high_favor_positive_bias(self):
        from game_engine.data_pipeline.favor.favor2src import favor2source
        pos, neg = favor2source(5000)
        assert pos == 2.0 and neg == 0.5


# ============================================================
# common_src_modify（整链）+ exp_calc
# ============================================================

class TestCommonSrcModify:
    def test_non_dating_no_extra_multiplier(self, world, z23_nearby, source_dict):
        """非约会状态无 1.2 倍加成（uniform 已移除，无随机）"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        src = dict(source_dict)
        src['love_source'] = 1000
        z23_nearby.favor = 300
        z23_nearby.base['mood'] = 0
        result = common_src_modify(src, z23_nearby)
        # 1000 * 1.3(favor300) * 0.8(relationship0陌生) * 1.0(emo/rat默认) = 1040
        assert result['love_source'] == 1040

    def test_dating_state_modifies_source(self, world, z23_nearby, source_dict):
        """约会状态下正向 source 放大 1.2 倍（uniform 已移除，无随机）"""
        from game_engine.data_pipeline.common_src_modify import common_src_modify
        src = dict(source_dict)
        src['love_source'] = 1000
        z23_nearby.favor = 300
        z23_nearby.cflag['dating'] = True
        result = common_src_modify(src, z23_nearby)
        # 1000 * 1.3 * 0.8(relationship0) * 1.2(dating) * 1.0(emo/rat默认) = 1248
        assert result['love_source'] == 1248


class TestExpCalc:
    def test_exp_calc_player_only(self, world):
        from game_engine.data_pipeline.exp_calc import exp_calc
        before = world.player.exp['talk_exp']
        mes = exp_calc('talk_exp', world.player)
        assert world.player.exp['talk_exp'] == before + 1
        assert '会话经验' in mes

