from game_engine.models.character import Character
from palam_config import PALAM_LV
from abl_config import EXP_LV

JUEL_GET: dict[int, int] = {
    PALAM_LV[1]: 0,
    PALAM_LV[1] * 3 // 2: 5,
    PALAM_LV[2]: 10,
    PALAM_LV[2] * 3 // 2: 20,
    PALAM_LV[3]: 50,
    PALAM_LV[3] * 3 // 2: 100,
    PALAM_LV[4]: 200,
    PALAM_LV[5]: 500,
    PALAM_LV[6]: 1000,
    PALAM_LV[7]: 2000,
    PALAM_LV[8]: 3500,
    PALAM_LV[9]: 6000,
    PALAM_LV[10]: 10_000,
    PALAM_LV[11]: 20_000,
    PALAM_LV[12]: 35_000,
    PALAM_LV[13]: 60_000,
    PALAM_LV[14]: 100_000,
    PALAM_LV[15]: 200_000,
    PALAM_LV[16]: 400_000,
    PALAM_LV[17]: 800_000,
    PALAM_LV[18]: 1_500_000,
    PALAM_LV[19]: 3_000_000,
    PALAM_LV[20]: 6_000_000,
    PALAM_LV[21]: 10_000_000,
    PALAM_LV[22]: 20_000_000,
    PALAM_LV[23]: 35_000_000,
    PALAM_LV[24]: 60_000_000,
    PALAM_LV[25]: 100_000_000
}

JUEL_SET: set[str] = {
    'c_pleasure_juel', 'v_pleasure_juel', 'a_pleasure_juel',
    'b_pleasure_juel', 'm_pleasure_juel', 'lust_juel',
    'obedience_juel', 'submission_juel', 'pain_juel',
    'kindness_juel', 'fear_juel', 'learn_juel',
    'depression_juel', 'disgust_juel', 'shame_juel',
    'unhappiness_juel', 'negation_juel'
}

BASE_PLEASURE_JUEL_DEMAND = {
    0: 1,
    1: 20,
    2: 400,
    3: 5_000,
    4: 15_000,
    5: 30_000,
    6: 40_000,
    7: 50_000,
    8: 60_000,
    9: 70_000
}

BASE_INTIMACY_JUEL_DEMAND = {
    0: 30,
    1: 100,
    2: 300,
    3: 1_000,
    4: 3_000,
    5: 10_000,
    6: 20_000,
    7: 35_000,
    8: 60_000,
    9: 100_000,
    10: 150_000,
    11: 250_000,
    12: 400_000,
    13: 650_000,
    14: 1_000_000,
    15: 1_500_000,
    16: 2_500_000,
    17: 4_000_000,
    18: 6_500_000,
    19: 10_000_000,
    20: 16_000_000
}

BASE_OBEDIENCE_FEAR_JUEL_DEMAND = {
    0: 30,
    1: 100,
    2: 1_000,
    3: 5_000,
    4: 7_500,
    5: 10_000,
    6: 15_000,
    7: 20_000,
    8: 25_000,
    9: 30_000
}

BASE_OBEDIENCE_OBEDIENCE_JUEL_DEMAND = {
    0: 30,
    1: 200,
    2: 1_000,
    3: 5_000,
    4: 7_500,
    5: 15_000,
    6: 25_000,
    7: 40_000,
    8: 50_000,
    9: 80_000,
    10: 100_000,
    11: 150_000,
    12: 250_000,
    13: 400_000,
    14: 600_000
}

BASE_OBEDIENCE_LUST_JUEL_DEMAND = {
    0: 150,
    1: 450,
    2: 1_000
}

BASE_OBEDIENCE_SUBMISSION_JUEL_DEMAND = {
    0: 100,
    1: 600,
    2: 1_200
}

BASE_DESIRE_JUEL_DEMAND = {
    0: 1,
    1: 20,
    2: 1_000,
    3: 8_000,
    4: 24_000,
    5: 30_000,
    6: 40_000,
    7: 50_000,
    8: 75_000,
    9: 100_000
}

BASE_SKILL_JUEL_DEMAND = {
    0: 1,
    1: 20,
    2: 200,
    3: 3000,
    4: 20_000,
    5: 25_000,
    6: 34_000,
    7: 45_000,
    8: 55_000,
    9: 70_000
}

BASE_SERVANT_SUBMISSION_JUEL_DEMAND = {
    0: 100,
    1: 1200,
    2: 5_000,
    3: 10_000,
    4: 30_000,
    5: 35_000,
    6: 40_000,
    7: 45_000,
    8: 50_000,
    9: 60_000
}

BASE_SERVANT_OBEDIENCE_JUEL_DEMAND = {
    0: 20,
    1: 100,
    2: 600,
    3: 2_000,
    4: 8_000,
    5: 8_500,
    6: 10_000,
    7: 15_000,
    8: 20_000,
    9: 30_000
}

BASE_EXPOSURE_JUEL_DEMAND = {
    0: 100,
    1: 500,
    2: 1500,
    3: 3_000,
    4: 6_000,
    5: 10_000,
    6: 15_000,
    7: 24_000,
    8: 30_000,
    9: 40_000
}

BASE_MASOCHISTIC_PAIN_JUEL_DEMAND = {
    0: 100,
    1: 300,
    2: 1_000,
    3: 6_000,
    4: 12_000,
    5: 15_000,
    6: 20_000,
    7: 25_000,
    8: 30_000,
    9: 40_000
}

BASE_MASOCHISTIC_LUST_JUEL_DEMAND = {
    0: 100,
    1: 500,
    2: 1_500,
    3: 3_000,
    4: 5_000,
    5: 8_000,
    6: 12_000,
    7: 16_000,
    8: 20_000,
    9: 30_000
}

BASE_MASOCHISTIC_SUBMISSION_JUEL_DEMAND = {
    0: 100,
    1: 500,
    2: 1_200
}

BASE_SADISM_JUEL_DEMAND = {
    0: 100,
    1: 500,
    2: 1_500,
    3: 3_000,
    4: 5_000,
    5: 8_000,
    6: 12_000,
    7: 15_000,
    8: 25_000,
    9: 30_000
}

BASE_MASTURBATION_ADDICTION_LUST_JUEL_DEMAND = {
    0: 1_000,
    1: 2_000,
    2: 3_000,
    3: 10_000,
    4: 15_000,
    5: 25_000,
    6: 30_000,
    7: 50_000,
    8: 60_000,
    9: 70_000
}

BASE_MASTURBATION_ADDICTION_C_PLEASURE_JUEL_DEMAND = {
    0: 5_000,
    1: 10_000,
    2: 30_000,
    3: 50_000,
    4: 100_000,
    5: 150_000,
    6: 200_000,
    7: 250_000,
    8: 300_000,
    9: 500_000
}

BASE_MASTURBATION_ADDICTION_SHAME_JUEL_DEMAND = {
    0: 1_000,
    1: 3_000,
    2: 5_000,
    3: 12_000,
    4: 20_000,
    5: 25_000,
    6: 40_000,
    7: 50_000,
    8: 60_000,
    9: 70_000
}

BASE_SEMEN_ADDICTION_LUST_JUEL_DEMAND = {
    0: 3_000,
    1: 8_000,
    2: 15_000,
    3: 30_000,
    4: 45_000,
    5: 60_000,
    6: 65_000,
    7: 70_000,
    8: 75_000,
    9: 90_000
}

BASE_SEMEN_ADDICTION_SUBMISSION_JUEL_DEMAND = {
    0: 10_000,
    1: 25_000,
    2: 50_000,
    3: 100_000,
    4: 300_000,
    5: 350_000,
    6: 400_000,
    7: 450_000,
    8: 500_000,
    9: 600_000
}

BASE_V_A_SEMEN_ADDICTION_LUST_JUEL_DEMAND = {
    0: 3_000,
    1: 8_000,
    2: 15_000,
    3: 30_000,
    4: 45_000,
    5: 60_000,
    6: 65_000,
    7: 70_000,
    8: 75_000,
    9: 90_000
}

BASE_V_A_SEMEN_ADDICTION_SUBMISSION_JUEL_DEMAND = {
    0: 10_000,
    1: 25_000,
    2: 50_000,
    3: 100_000,
    4: 300_000,
    5: 350_000,
    6: 400_000,
    7: 450_000,
    8: 500_000,
    9: 600_000
}


def get_juel_demand(chara: Character) -> dict[str, dict[str, int]]:
    return {
        'c_sen_abl': c_pleasure_juel_demand(chara),
        'v_sen_abl': v_pleasure_juel_demand(chara),
        'a_sen_abl': a_pleasure_juel_demand(chara),
        'b_sen_abl': b_pleasure_juel_demand(chara),
        'm_sen_abl': m_pleasure_juel_demand(chara),
        'intimacy_abl': intimacy_juel_demand(chara),
        'obedience_abl': obedience_juel_demand(chara),
        'desire_abl': desire_juel_demand(chara),
        'skill_abl': skill_juel_demand(chara),
        'servant_abl': servant_juel_demand(chara),
        'exposure_abl': exposure_juel_demand(chara),
        'masochistic_abl': masochistic_juel_demand(chara),
        'sadism_abl': sadism_juel_demand(chara),
        'masturbation_addiction_abl': masturbation_addiction_juel_demand(chara),
        'semen_addiction_abl': semen_addiction_juel_demand(chara),
        'v_semen_addiction_abl': v_semen_addiction_juel_demand(chara),
        'a_semen_addiction_abl': a_semen_addiction_juel_demand(chara)
    }


def c_pleasure_juel_demand(chara: Character):
    """C感度"""
    demand = BASE_PLEASURE_JUEL_DEMAND.get(chara.abl['c_sen_abl'], 20_000 * (chara.abl['c_sen_abl'] - 6))
    # 经验补正
    demand = get_base_exp_modify(chara, demand, 'c')
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 快C之珠
    return {'c_pleasure_juel': int(demand)}


def v_pleasure_juel_demand(chara: Character):
    """V感度"""
    demand = BASE_PLEASURE_JUEL_DEMAND.get(chara.abl['v_sen_abl'], 20_000 * (chara.abl['v_sen_abl'] - 6))
    # 经验补正
    demand *= get_expand_modify(chara.exp['v_expand_exp'])
    demand = get_base_exp_modify(chara, demand, 'v')
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 快V之珠
    return {'v_pleasure_juel': int(demand)}


def a_pleasure_juel_demand(chara: Character):
    """A感度"""
    demand = BASE_PLEASURE_JUEL_DEMAND.get(chara.abl['a_sen_abl'], 20_000 * (chara.abl['a_sen_abl'] - 6))
    # 经验补正
    demand *= get_expand_modify(chara.exp['a_expand_exp'])
    demand = get_base_exp_modify(chara, demand, 'a')
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 快A之珠
    return {'a_pleasure_juel': int(demand)}


def b_pleasure_juel_demand(chara: Character):
    """B感度"""
    demand = BASE_PLEASURE_JUEL_DEMAND.get(chara.abl['b_sen_abl'], 20_000 * (chara.abl['b_sen_abl'] - 6))
    # 经验补正
    demand = get_base_exp_modify(chara, demand, 'b')
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 快B之珠
    return {'b_pleasure_juel': int(demand)}


def m_pleasure_juel_demand(chara: Character):
    """M感度"""
    demand = BASE_PLEASURE_JUEL_DEMAND.get(chara.abl['m_sen_abl'], 20_000 * (chara.abl['m_sen_abl'] - 6))
    # 经验补正
    demand = get_base_exp_modify(chara, demand, 'm')
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 快M之珠
    return {'m_pleasure_juel': int(demand)}


def intimacy_juel_demand(chara: Character):
    """亲密"""
    demand = BASE_INTIMACY_JUEL_DEMAND.get(chara.abl['intimacy_abl'], 40_000 * (chara.abl['intimacy_abl'] ** 2))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara, True)
    # 好意之珠
    return {'kindness_juel': int(demand)}


def obedience_juel_demand(chara: Character):
    """顺从"""
    fear_demand = BASE_OBEDIENCE_FEAR_JUEL_DEMAND.get(chara.abl['obedience_abl'],
                                                      10_000 * (chara.abl['obedience_abl'] - 6))
    obedience_demand = BASE_OBEDIENCE_OBEDIENCE_JUEL_DEMAND.get(chara.abl['obedience_abl'],
                                                                4_000 * (chara.abl['obedience_abl'] ** 2))
    lust_demand = BASE_OBEDIENCE_LUST_JUEL_DEMAND.get(chara.abl['obedience_abl'], -1)
    submission_demand = BASE_OBEDIENCE_SUBMISSION_JUEL_DEMAND.get(chara.abl['obedience_abl'], -1)

    # 陷落阶段
    obedience_demand *= (10 - 2 * chara.get_talent_value('relationship')) / 10
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        fear_demand *= impassable_line_modify(chara)
        obedience_demand *= impassable_line_modify(chara)
        lust_demand *= impassable_line_modify(chara)
        submission_demand *= impassable_line_modify(chara)
    # 恐怖之珠/顺从之珠/欲情之珠/屈服之珠
    return {'fear_juel': int(fear_demand),
            'obedience_juel': int(obedience_demand),
            'lust_juel': int(lust_demand),
            'submission_juel': int(submission_demand)
            }


def desire_juel_demand(chara: Character):
    """欲望"""
    demand = BASE_DESIRE_JUEL_DEMAND.get(chara.abl['desire_abl'], 150_000 * (chara.abl['desire_abl'] - 8))
    # 陷落阶段
    demand *= (10 - 2 * chara.get_talent_value('relationship')) / 10
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 欲情之珠
    return {'lust_juel': int(demand)}


def skill_juel_demand(chara: Character):
    """技巧"""
    demand = BASE_SKILL_JUEL_DEMAND.get(chara.abl['skill_abl'], 10_000 + 20_000 * (chara.abl['skill_abl'] - 6))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 技巧之珠
    return {'learn_juel': int(demand)}


def servant_juel_demand(chara: Character):
    """侍奉精神"""
    submission_demand = BASE_SERVANT_OBEDIENCE_JUEL_DEMAND.get(chara.abl['servant_abl'],
                                                               10_000 + 20_000 * (chara.abl['servant_abl'] - 7))
    obedience_demand = BASE_SERVANT_OBEDIENCE_JUEL_DEMAND.get(chara.abl['servant_abl'],
                                                              10_000 + 20_000 * (chara.abl['servant_abl'] - 7))
    learn_demand = 100 if chara.abl['servant_abl'] == 0 else -1
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        submission_demand *= impassable_line_modify(chara)
        obedience_demand *= impassable_line_modify(chara)
        learn_demand *= impassable_line_modify(chara)
    # 侍奉之珠/顺从之珠/习得之珠
    return {'submission_juel': int(submission_demand),
            'obedience_juel': int(obedience_demand),
            'learn_juel': int(learn_demand)
            }


def exposure_juel_demand(chara: Character):
    """露出癖"""
    demand = BASE_EXPOSURE_JUEL_DEMAND.get(chara.abl['exposure_abl'], 20_000 * (chara.abl['exposure_abl'] - 7))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 羞耻之珠
    return {'shame_juel': int(demand)}


def masochistic_juel_demand(chara: Character):
    """受虐属性"""
    pain_demand = BASE_MASOCHISTIC_PAIN_JUEL_DEMAND.get(chara.abl['masochistic_abl'],
                                                        10_000 * (chara.abl['masochistic_abl'] - 5))
    lust_demand = BASE_MASOCHISTIC_LUST_JUEL_DEMAND.get(chara.abl['masochistic_abl'],
                                                        10_000 * (chara.abl['masochistic_abl'] - 6))
    submission_demand = BASE_MASOCHISTIC_SUBMISSION_JUEL_DEMAND.get(chara.abl['masochistic_abl'], -1)
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        pain_demand *= impassable_line_modify(chara)
        lust_demand *= impassable_line_modify(chara)
        submission_demand *= impassable_line_modify(chara)
    # 受虐狂
    if chara.has_talent('masochism'):
        pain_demand *= 0.5
        lust_demand *= 0.5
        submission_demand *= 0.5
    # 苦痛之珠/欲情之珠/屈服之珠
    return {'pain_juel': int(pain_demand),
            'lust_juel': int(lust_demand),
            'submission_juel': int(submission_demand)
            }


def sadism_juel_demand(chara: Character):
    """施虐属性"""
    demand = BASE_SADISM_JUEL_DEMAND.get(chara.abl['sadism_abl'], 10_000 * (chara.abl['sadism_abl'] - 6))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        demand *= impassable_line_modify(chara)
    # 施虐狂
    if chara.has_talent('sadism'):
        demand *= 0.5
    # 欲情之珠
    return {'lust_juel': int(demand)}


def masturbation_addiction_juel_demand(chara: Character):
    """自慰中毒"""
    # C感度限制
    if chara.abl['c_sen_abl'] < chara.abl['masturbation_addiction_abl']:
        return {'lust_juel': -1}
    # 露出癖限制
    if chara.abl['exposure_abl'] < chara.abl['masturbation_addiction_abl']:
        return {'shame_juel': -1}
    lust_demand = BASE_MASTURBATION_ADDICTION_LUST_JUEL_DEMAND.get(chara.abl['masturbation_addiction_abl'], 10_000 * (
            chara.abl['masturbation_addiction_abl'] - 2))
    c_pleasure_demand = BASE_MASTURBATION_ADDICTION_C_PLEASURE_JUEL_DEMAND.get(chara.abl['masturbation_addiction_abl'],
                                                                               100_000 * (chara.abl[
                                                                                              'masturbation_addiction_abl'] - 3))
    shame_demand = BASE_MASTURBATION_ADDICTION_SHAME_JUEL_DEMAND.get(chara.abl['masturbation_addiction_abl'],
                                                                     10_000 * (chara.abl[
                                                                                   'masturbation_addiction_abl'] - 2))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        lust_demand *= impassable_line_modify(chara)
        c_pleasure_demand *= impassable_line_modify(chara)
        shame_demand *= impassable_line_modify(chara)
    # 容易中毒
    if chara.has_talent('easy_to_addicted'):
        lust_demand *= 0.5
        c_pleasure_demand *= 0.5
        shame_demand *= 0.5
    # 自慰中毒之珠/欲情之珠/羞耻之珠
    return {'lust_juel': int(lust_demand),
            'c_pleasure_juel': int(c_pleasure_demand),
            'shame_juel': int(shame_demand)
            }


def semen_addiction_juel_demand(chara: Character):
    """精液中毒"""
    lust_demand = BASE_SEMEN_ADDICTION_LUST_JUEL_DEMAND.get(chara.abl['semen_addiction_abl'],
                                                            15_000 * (chara.abl['semen_addiction_abl'] - 3))
    submission_demand = BASE_SEMEN_ADDICTION_SUBMISSION_JUEL_DEMAND.get(chara.abl['semen_addiction_abl'], 100_000 * (
            chara.abl['semen_addiction_abl'] - 3))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        lust_demand *= impassable_line_modify(chara)
        submission_demand *= impassable_line_modify(chara)
    # 容易中毒
    if chara.has_talent('easy_to_addicted'):
        lust_demand *= 0.5
        submission_demand *= 0.5
    return {'lust_juel': int(lust_demand),
            'submission_juel': int(submission_demand)
            }


def v_semen_addiction_juel_demand(chara: Character):
    """穴射中毒"""
    # 精液中毒限制
    if chara.abl['semen_addiction_abl'] < chara.abl['v_semen_addiction_abl']:
        return {'lust_juel': -1}
    lust_demand = BASE_V_A_SEMEN_ADDICTION_LUST_JUEL_DEMAND.get(chara.abl['v_semen_addiction_abl'],
                                                                15_000 * (chara.abl['v_semen_addiction_abl'] - 3))
    submission_demand = BASE_V_A_SEMEN_ADDICTION_SUBMISSION_JUEL_DEMAND.get(chara.abl['v_semen_addiction_abl'],
                                                                            100_000 * (
                                                                                    chara.abl[
                                                                                        'v_semen_addiction_abl'] - 3
                                                                            ))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        lust_demand *= impassable_line_modify(chara)
        submission_demand *= impassable_line_modify(chara)
    # 容易中毒
    if chara.has_talent('easy_to_addicted'):
        lust_demand *= 0.5
        submission_demand *= 0.5
    # V感度
    if chara.has_talent('v_sensitivity'):
        lust_demand *= 0.5
        submission_demand *= 0.5
    # 欲情之珠/屈服之珠
    return {
        'lust_juel': int(lust_demand),
        'submission_juel': int(submission_demand)
    }


def a_semen_addiction_juel_demand(chara: Character):
    """肛射中毒"""
    # 精液中毒限制
    if chara.abl['semen_addiction_abl'] < chara.abl['v_semen_addiction_abl']:
        return {'lust_juel': -1}
    lust_demand = BASE_V_A_SEMEN_ADDICTION_LUST_JUEL_DEMAND.get(chara.abl['v_semen_addiction_abl'],
                                                                15_000 * (chara.abl['v_semen_addiction_abl'] - 3))
    submission_demand = BASE_V_A_SEMEN_ADDICTION_SUBMISSION_JUEL_DEMAND.get(chara.abl['v_semen_addiction_abl'],
                                                                            100_000 * (
                                                                                    chara.abl[
                                                                                        'v_semen_addiction_abl'] - 3
                                                                            ))
    # 难以逾越的底线
    if chara.has_talent('impassable_line'):
        lust_demand *= impassable_line_modify(chara)
        submission_demand *= impassable_line_modify(chara)
    # 容易中毒
    if chara.has_talent('easy_to_addicted'):
        lust_demand *= 0.5
        submission_demand *= 0.5
    # A感度
    if chara.has_talent('a_sensitivity'):
        lust_demand *= 0.5
        submission_demand *= 0.5
    # 欲情之珠/屈服之珠
    return {
        'lust_juel': int(lust_demand),
        'submission_juel': int(submission_demand)
    }


def get_expand_modify(exp: int):
    if exp > 50:
        return 0.5
    elif exp > 40:
        return 0.6
    elif exp > 30:
        return 0.7
    elif exp > 20:
        return 0.8
    elif exp > 10:
        return 0.9
    return 0.95


def impassable_line_modify(chara: Character, friendship: bool = False):
    # 关系在喜欢以下
    if chara.get_talent_value('relationship') < 2:
        if chara.get_talent_value('relationship') == 1 and friendship:
            # 关系式友好且abl受到友好影响
            return 1
        return 2
    else:
        return 0.5


def get_base_exp_modify(chara: Character, demand: int | float, kind: str):
    demand *= 10 / (5 + EXP_LV[chara.exp[f'{kind}_exp']])
    demand *= (1 + chara.abl[f'{kind}_sen_abl']) / (1 + EXP_LV[chara.exp[f'{kind}_orgasm_exp']])
    return demand
