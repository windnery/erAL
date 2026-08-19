# -*- coding: utf-8 -*-
"""改进阶段回归测试：锁定对“明显不合理点”的修复

覆盖：
1. 关系（relationship）升到[爱]后不再每日重复播报“关系变成[爱]”
2. 肛射中毒（a_semen_addiction）升级需求读取正确的 a_semen_addiction_abl
3. attr_defs 中 base 显示名无重复（energy=气力 / vitality=精力）
4. get_attitude 合意判定明细正确输出天赋相关加减分
"""
from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import get_attitude
from game_engine.data_pipeline.talent.talent_check import talent_check


def test_relationship_already_love_does_not_repeat(world):
    """关系已是[爱](3)时，日终 talent 检查不再重复播报，也不降级"""
    z23 = world.npc_manager.shipgirls['Z23']
    z23.set_talent('relationship', '3')
    z23.favor = 3000
    z23.trust = 600
    z23.abl['intimacy_abl'] = 9

    mes = talent_check(world, z23)

    assert mes == []
    assert z23.get_talent_value('relationship') == 3


def test_relationship_advances_when_qualified(world):
    """满足门槛时关系应正常升级（至少升到友好）"""
    z23 = world.npc_manager.shipgirls['Z23']
    z23.set_talent('relationship', '0')
    z23.favor = 3000
    z23.trust = 600
    z23.abl['intimacy_abl'] = 9

    mes = talent_check(world, z23)

    assert z23.get_talent_value('relationship') >= 1
    assert mes


def test_a_semen_demand_uses_a_sen_abl(world):
    """肛射中毒的升级需求应随 a_semen_addiction_abl 变化（而非 v_semen_addiction_abl）"""
    from config.juel_config import a_semen_addiction_juel_demand

    ayanami = world.npc_manager.shipgirls['ayanami']
    ayanami.abl['semen_addiction_abl'] = 1
    ayanami.abl['v_semen_addiction_abl'] = 0
    ayanami.abl['a_semen_addiction_abl'] = 0
    d0 = a_semen_addiction_juel_demand(ayanami)

    ayanami.abl['a_semen_addiction_abl'] = 1
    d1 = a_semen_addiction_juel_demand(ayanami)

    assert d0['lust_juel'] == 3000
    assert d1['lust_juel'] == 8000
    assert d0 != d1


def test_attr_defs_base_names_unique_and_energy_is_qi_li():
    """base 显示名无重复；energy 为“气力”，vitality 为“精力”"""
    base = ATTR_DEFS['base']
    names = [v['name'] for v in base.values()]

    assert len(names) == len(set(names)), f'base 显示名重复: {names}'
    assert base['energy']['name'] == '气力'
    assert base['max_energy']['name'] == '最大气力'
    assert base['vitality']['name'] == '精力'


def test_get_attitude_includes_talent_factor(world):
    """合意判定明细应包含天赋导致的加减分（绫波带“冷漠”）"""
    ayanami = world.npc_manager.shipgirls['ayanami']
    assert ayanami.has_talent('indifference')

    mes, attitude = get_attitude(world.player, ayanami, 0)

    assert '冷漠' in mes
    assert attitude < 0
