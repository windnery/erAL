from config.abl_config import ABL_LV
from config.attr_defs import ATTR_DEFS
from config.base_config import MAX_EMOTION
from game_engine.managers.NpcManager import NpcManager
from game_engine.models.character import Character
from game_engine.models.shipgirl import ShipGirl


def palam_calc(src: dict[str, int], source: Character, target: Character, dry_run: bool = False):
    """将source转成palam
    dry_run: 只计算增量不应用，返回 changes 供外部聚合（配合 source_proc_batch 使用）
    返回：(mes_source, mes_target, changes)
        changes: dict[(chara_kind, palam), delta]，chara_kind 为 'source' 或 'target'
    """
    mes_source: list[str] = [f'{source.name}']
    mes_target: list[str] = [f'{target.name}']
    changes: dict[tuple[str, str], int] = {}

    palam_dict_list: list[dict[str, dict[str, str | int]]] = []
    palam_dict_list.append(c_pleasure_source(src, target))
    palam_dict_list.append(v_pleasure_source(src, target))
    palam_dict_list.append(a_pleasure_source(src, target))
    palam_dict_list.append(b_pleasure_source(src, target))
    palam_dict_list.append(m_pleasure_source(src, target))
    palam_dict_list.append(love_source(src, target))
    palam_dict_list.append(sex_act_source(src, target))
    palam_dict_list.append(achievement_source(src, target))
    palam_dict_list.append(pain_source(src, source, target))
    palam_dict_list.append(fear_source(src, target))
    palam_dict_list.append(lubrication_source(src, target))
    palam_dict_list.append(lust_source(src, target))
    palam_dict_list.append(obedience_source(src, target))
    palam_dict_list.append(exposure_source(src, target))
    palam_dict_list.append(submission_source(src, target))
    palam_dict_list.append(happiness_source(src, target))
    palam_dict_list.append(conquest_source(src, target))
    palam_dict_list.append(passivity_source(src, target))
    palam_dict_list.append(unclean_source(src, target))
    palam_dict_list.append(depression_source(src, target))
    palam_dict_list.append(escape_source(src, target))
    palam_dict_list.append(disgust_source(src, target))

    # 聚合：按 (chara, palam) 求和
    merged: dict[tuple[str, str], int] = {}
    for palam_dict in palam_dict_list:
        for palam, info in palam_dict.items():
            key = (info['chara'], palam)  # ('target', 'lust_palam')
            merged[key] = merged.get(key, 0) + int(info['value'])

    if dry_run:
        # 只返回增量，不改 palam
        changes = merged
    else:
        # 统一应用 + 打印
        for (chara_kind, palam), value in merged.items():
            if value == 0:
                continue
            chara = source if chara_kind == 'source' else target
            mes = f'{ATTR_DEFS["palam"][palam]["name"]} {chara.palam[palam]} + {value} = {chara.palam[palam] + value}'
            (mes_source if chara_kind == 'source' else mes_target).append(mes)
            chara.palam[palam] += value

        if len(mes_source) == 1:
            mes_source = []
        if len(mes_target) == 1:
            mes_target = []

    return mes_source, mes_target, changes


def c_pleasure_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理c_pleasure_source
        return: 快C 欲情"""
    c_pleasure_source = source.get('c_pleasure_source', 0)
    # talent: C感度
    c_sensitivity = target.get_talent_value('c_sensitivity')
    c_pleasure_source *= {-1: 0.7, 0: 1, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0, 5: 4.0}[c_sensitivity]
    # abl: C感觉
    c_sen_abl = target.abl['c_sen_abl']
    c_pleasure_source *= p_source_revision(c_sen_abl, True) / 10
    # palam_lv: 欲情
    if target.palam_lv['lust_palam'] < 1:
        c_pleasure_source *= 0.8
    elif target.palam_lv['lust_palam'] < 3:
        pass
    elif target.palam_lv['lust_palam'] < 5:
        c_pleasure_source *= 1.2
    elif target.palam_lv['lust_palam'] < 7:
        c_pleasure_source *= 1.4
    else:
        c_pleasure_source *= 1.6

    lust_source = c_pleasure_source
    lust_source *= p_source_revision(target.abl['desire_abl'], False) / 100
    lubrication_source = c_pleasure_source * 0.1

    return {
        'c_pleasure_palam': {'chara': 'target', 'value': int(c_pleasure_source)},
        'lust_palam': {'chara': 'target', 'value': int(lust_source)},
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }


def v_pleasure_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理v_pleasure_source
        return: 快V 欲情"""
    v_pleasure_source = source.get('v_pleasure_source', 0)
    # talent: V感度
    v_sensitivity = target.get_talent_value('v_sensitivity')
    v_pleasure_source *= {-1: 0.7, 0: 1, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0, 5: 4.0}[v_sensitivity]
    # abl: V感觉
    v_sen_abl = target.abl['v_sen_abl']
    v_pleasure_source *= p_source_revision(v_sen_abl, True) / 10
    # exp: V经验
    v_exp = target.exp['v_exp']
    if v_exp < ABL_LV[1]:
        v_pleasure_source *= 0.3
    elif v_exp < ABL_LV[2]:
        v_pleasure_source *= 0.5
    elif v_exp < ABL_LV[3]:
        v_pleasure_source *= 0.8
    elif v_exp < ABL_LV[4]:
        pass
    elif v_exp < ABL_LV[5]:
        v_pleasure_source *= 1.2
    else:
        v_pleasure_source *= 1.5
    # palam_lv: 润滑
    if target.palam_lv['lubrication_palam'] < 1:
        v_pleasure_source *= 0.1
    elif target.palam_lv['lubrication_palam'] < 2:
        v_pleasure_source *= 0.3
    elif target.palam_lv['lubrication_palam'] < 3:
        v_pleasure_source *= 0.4
    elif target.palam_lv['lubrication_palam'] < 4:
        v_pleasure_source *= 0.75
    elif target.palam_lv['lubrication_palam'] < 5:
        v_pleasure_source *= 0.9
    else:
        pass
    # palam_lv: 欲情
    if target.palam_lv['lust_palam'] < 1:
        v_pleasure_source *= 0.6
    elif target.palam_lv['lust_palam'] < 3:
        v_pleasure_source *= 0.8
    elif target.palam_lv['lust_palam'] < 5:
        pass
    elif target.palam_lv['lust_palam'] < 7:
        v_pleasure_source *= 1.2
    else:
        v_pleasure_source *= 1.5

    lust_source = v_pleasure_source
    lust_source *= p_source_revision(target.abl['desire_abl'], False) / 100
    lubrication_source = v_pleasure_source * 0.1

    return {
        'v_pleasure_palam': {'chara': 'target', 'value': int(v_pleasure_source)},
        'lust_palam': {'chara': 'target', 'value': int(lust_source)},
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }


def a_pleasure_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理v_pleasure_source
        return: 快A 欲情"""
    a_pleasure_source = source.get('a_pleasure_source', 0)
    # talent: A感度
    a_sensitivity = target.get_talent_value('a_sensitivity')
    a_pleasure_source *= {-1: 0.7, 0: 1, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0, 5: 4.0}[a_sensitivity]
    # abl: A感觉
    a_sen_abl = target.abl['a_sen_abl']
    a_pleasure_source *= p_source_revision(a_sen_abl, True) / 10
    # exp: A经验
    a_exp = target.exp['a_exp']
    if a_exp < ABL_LV[1]:
        a_pleasure_source *= 0.3
    elif a_exp < ABL_LV[2]:
        a_pleasure_source *= 0.5
    elif a_exp < ABL_LV[3]:
        a_pleasure_source *= 0.8
    elif a_exp < ABL_LV[4]:
        pass
    elif a_exp < ABL_LV[5]:
        a_pleasure_source *= 1.2
    else:
        a_pleasure_source *= 1.5
    # palam_lv: 润滑
    if target.palam_lv['lubrication_palam'] < 1:
        a_pleasure_source *= 0.1
    elif target.palam_lv['lubrication_palam'] < 2:
        a_pleasure_source *= 0.3
    elif target.palam_lv['lubrication_palam'] < 3:
        a_pleasure_source *= 0.4
    elif target.palam_lv['lubrication_palam'] < 4:
        a_pleasure_source *= 0.75
    elif target.palam_lv['lubrication_palam'] < 5:
        a_pleasure_source *= 0.9
    else:
        pass
    # palam_lv: 欲情
    if target.palam_lv['lust_palam'] < 1:
        a_pleasure_source *= 0.6
    elif target.palam_lv['lust_palam'] < 3:
        a_pleasure_source *= 0.8
    elif target.palam_lv['lust_palam'] < 5:
        pass
    elif target.palam_lv['lust_palam'] < 7:
        a_pleasure_source *= 1.2
    else:
        a_pleasure_source *= 1.5

    lust_source = a_pleasure_source
    lust_source *= p_source_revision(target.abl['desire_abl'], False) / 100
    lubrication_source = a_pleasure_source * 0.1

    return {
        'a_pleasure_palam': {'chara': 'target', 'value': int(a_pleasure_source)},
        'lust_palam': {'chara': 'target', 'value': int(lust_source)},
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }


def b_pleasure_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理b_pleasure_source
        return: 快B 欲情"""
    b_pleasure_source = source.get('b_pleasure_source', 0)
    # talent: B感度
    b_sensitivity = target.get_talent_value('b_sensitivity')
    b_pleasure_source *= {-1: 0.7, 0: 1, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0, 5: 4.0}[b_sensitivity]
    # abl: B感觉
    b_sen_abl = target.abl['b_sen_abl']
    b_pleasure_source *= p_source_revision(b_sen_abl, True) / 10
    # palam_lv: 欲情
    if target.palam_lv['lust_palam'] < 1:
        b_pleasure_source *= 0.8
    elif target.palam_lv['lust_palam'] < 3:
        pass
    elif target.palam_lv['lust_palam'] < 5:
        b_pleasure_source *= 1.2
    elif target.palam_lv['lust_palam'] < 7:
        b_pleasure_source *= 1.4
    else:
        b_pleasure_source *= 1.6

    lust_source = b_pleasure_source
    lust_source *= p_source_revision(target.abl['desire_abl'], False) / 100
    lubrication_source = b_pleasure_source * 0.1

    return {
        'b_pleasure_palam': {'chara': 'target', 'value': int(b_pleasure_source)},
        'lust_palam': {'chara': 'target', 'value': int(lust_source)},
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }


def m_pleasure_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理m_pleasure_source
        return: 快M 欲情"""
    m_pleasure_source = source.get('m_pleasure_source', 0)
    # talent: M感度
    m_sensitivity = target.get_talent_value('m_sensitivity')
    m_pleasure_source *= {-1: 0.7, 0: 1, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0, 5: 4.0}[m_sensitivity]
    # abl: M感觉
    m_sen_abl = target.abl['m_sen_abl']
    m_pleasure_source *= p_source_revision(m_sen_abl, True) / 10
    # exp: M经验
    m_exp = target.exp['m_exp']
    if m_exp < ABL_LV[1]:
        m_pleasure_source *= 0.3
    elif m_exp < ABL_LV[2]:
        m_pleasure_source *= 0.5
    elif m_exp < ABL_LV[3]:
        pass
    elif m_exp < ABL_LV[4]:
        m_pleasure_source *= 2.0
    elif m_exp < ABL_LV[5]:
        m_pleasure_source *= 3.0
    else:
        m_pleasure_source *= 5.0
    # palam_lv: 欲情
    if target.palam_lv['lust_palam'] < 1:
        m_pleasure_source *= 0.6
    elif target.palam_lv['lust_palam'] < 3:
        m_pleasure_source *= 0.8
    elif target.palam_lv['lust_palam'] < 5:
        pass
    elif target.palam_lv['lust_palam'] < 7:
        m_pleasure_source *= 1.2
    else:
        m_pleasure_source *= 1.5

    lust_source = m_pleasure_source
    lust_source *= p_source_revision(target.abl['desire_abl'], False) / 100
    lubrication_source = m_pleasure_source * 0.1

    return {
        'm_pleasure_palam': {'chara': 'target', 'value': int(m_pleasure_source)},
        'lust_palam': {'chara': 'target', 'value': int(lust_source)},
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }


def love_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理love_source
        return: 恭顺 欲情"""
    # TODO: 强行
    love_source = source.get('love_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    love_source_1 = abl_revision(love_source, target.abl['obedience_abl'], True)
    # abl: 欲望
    love_source_2 = abl_revision(love_source, target.abl['desire_abl'], False)
    return {
        'obedience_palam': {'chara': 'target', 'value': int(love_source_1)},
        'lust_palam': {'chara': 'target', 'value': int(love_source_2)}
    }


def sex_act_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理sex_act_source
        return: 习得"""
    sex_act_source = source.get('sex_act_source', 0)
    # TODO: 对方主导
    # abl: 技巧
    sex_act_source = abl_revision(sex_act_source, target.abl['skill_abl'], True)
    # abl: 侍奉精神
    match target.abl['servant_abl']:
        case 0:
            sex_act_source *= 0.6
        case 1:
            sex_act_source *= 0.8
        case 2:
            sex_act_source *= 1.0
        case 3:
            sex_act_source *= 1.2
        case 4:
            sex_act_source *= 1.4
        case 5:
            sex_act_source *= 1.7
        case 6:
            sex_act_source *= 2.0
        case 7:
            sex_act_source *= 2.4
        case 8:
            sex_act_source *= 2.8
        case 9:
            sex_act_source *= 4.0
        case _:
            sex_act_source *= 5.0
    return {
        'learn_palam': {'chara': 'target', 'value': int(sex_act_source)}
    }


def achievement_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理achievement_source
        return: 恭顺"""
    achievement_source = source.get('achievement_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    achievement_source = abl_revision(achievement_source, target.abl['obedience_abl'], True)
    # abl: 侍奉精神
    achievement_source = abl_revision(achievement_source, target.abl['servant_abl'], False)
    return {
        'obedience_palam': {'chara': 'target', 'value': int(achievement_source)}
    }


def pain_source(source: dict[str, int], actor: Character, target: Character) -> dict[str, dict[str, str | int]]:
    """处理pain_source
        return: 苦痛 欲情 恐惧"""
    pain_source2pain = source.get('pain_source', 0)
    pain_source2lust = source.get('pain_source', 0)
    pain_source2fear = source.get('pain_source', 0) // 20

    # abl: 受虐属性
    match target.abl['masochistic_abl']:
        case 0:
            pain_source2lust = 0
        case 1:
            pain_source2lust *= 0.1
        case 2:
            pain_source2lust *= 0.2
        case 3:
            pain_source2lust *= 0.3
        case 4:
            pain_source2lust *= 0.45
        case 5:
            pain_source2lust *= 0.6
        case 6:
            pain_source2lust *= 0.75
        case 7:
            pain_source2lust *= 0.9
        case 8:
            pain_source2lust *= 1.2
        case 9:
            pain_source2lust *= 1.5
        case _:
            pain_source2lust *= 3.0
    # TODO: 体型
    # 调教者施虐狂
    if actor.has_talent('sadism'):
        pain_source2lust *= 2.5
    # 胆怯
    if target.get_talent_value('courage'):
        pain_source2fear *= 2.0
    return {
        'pain_palam': {'chara': 'target', 'value': int(pain_source2pain)},
        'lust_palam': {'chara': 'target', 'value': int(pain_source2lust)},
        'fear_palam': {'chara': 'target', 'value': int(pain_source2fear)}
    }


def fear_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理fear_source
        return: 恐惧"""
    fear_source = source.get('fear_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    fear_source = abl_revision(fear_source, target.abl['obedience_abl'], True)
    return {
        'fear_palam': {'chara': 'target', 'value': int(fear_source)}
    }


def lubrication_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理lubrication_source
        return: 润滑"""
    lubrication_source = source.get('lubrication_source', 0)
    # TODO: 体型
    return {
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }


def lust_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理lust_source
        return: 欲情"""
    lust_source = source.get('lust_source', 0)
    # TODO: 发情
    # abl: 欲望
    lust_source = abl_revision(lust_source, target.abl['desire_abl'], False)
    return {
        'lust_palam': {'chara': 'target', 'value': int(lust_source)}
    }


def obedience_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理obedience_source
        return: 恭顺"""
    obedience_source = source.get('obedience_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    match target.abl['obedience_abl']:
        case 0:
            obedience_source *= 0.5
        case 1:
            obedience_source *= 0.8
        case 2:
            obedience_source *= 1.0
        case 3:
            obedience_source *= 1.2
        case 4:
            obedience_source *= 1.4
        case 5:
            obedience_source *= 1.6
        case 6:
            obedience_source *= 1.8
        case 7:
            obedience_source *= 2.0
        case 8:
            obedience_source *= 2.4
        case 9:
            obedience_source *= 3.0
        case _:
            obedience_source *= 5.0
    return {
        'obedience_palam': {'chara': 'target', 'value': int(obedience_source)}
    }


def exposure_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理exposure_source
        return: 欲情 羞耻"""
    exposure_source_1 = source.get('exposure_source', 0)
    exposure_source_2 = source.get('exposure_source', 0)
    # 害羞和不知羞耻
    if target.get_talent_value('sense_of_shame') > 0:
        exposure_source_1 *= 2.0
    elif target.get_talent_value('sense_of_shame') < 0:
        exposure_source_1 *= 0.5
    # 有旁人在场
    if NpcManager.with_mob(target.location['region'], target.location['node']):
        exposure_source_1 *= 1.5
    # 润滑追加露出
    exposure_source_1 += source.get('lubrication_source', 0) // 2
    # TODO: 对方主导
    # abl: 露出癖
    match target.abl['exposure_abl']:
        case 0:
            exposure_source_1 = 0
        case 1:
            exposure_source_1 *= 0.1
        case 2:
            exposure_source_1 *= 0.2
        case 3:
            exposure_source_1 *= 0.4
        case 4:
            exposure_source_1 *= 0.6
        case 5:
            exposure_source_1 *= 0.8
        case 6:
            exposure_source_1 *= 1.0
        case 7:
            exposure_source_1 *= 1.2
        case 8:
            exposure_source_1 *= 1.4
        case 9:
            exposure_source_1 *= 1.6
        case _:
            exposure_source_1 *= 2.0
    # 羞耻追加
    if target.palam_lv['shame_palam'] < 1:
        pass
    elif target.palam_lv['shame_palam'] < 2:
        exposure_source_2 *= 0.9
    elif target.palam_lv['shame_palam'] < 3:
        exposure_source_2 *= 0.8
    elif target.palam_lv['shame_palam'] < 4:
        exposure_source_2 *= 0.7
    else:
        exposure_source_2 *= 0.6

    return {
        'lust_palam': {'chara': 'target', 'value': int(exposure_source_1)},
        'shame_palam': {'chara': 'target', 'value': int(exposure_source_2)}
    }


def submission_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理submission_source
        return: 屈服"""
    submission_source = source.get('submission_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    submission_source = abl_revision(submission_source, target.abl['obedience_abl'], True)
    # abl: 侍奉精神
    match target.abl['servant_abl']:
        case 0:
            pass
        case 1:
            submission_source *= 1.5
        case 2:
            submission_source *= 2.0
        case 3:
            submission_source *= 2.5
        case 4:
            submission_source *= 3.0
        case 5:
            submission_source *= 3.5
        case 6:
            submission_source *= 4.0
        case 7:
            submission_source *= 4.5
        case 8:
            submission_source *= 5.0
        case 9:
            submission_source *= 5.5
        case _:
            submission_source *= 7.0
    return {
        'submission_palam': {'chara': 'target', 'value': int(submission_source)}
    }


def happiness_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理happiness_source
        return: target好意 player欲情"""
    happiness_source = source.get('happiness_source', 0)
    # TODO: 对方主导
    # 陷落素质
    happiness_source *= 10 + 3 * target.get_talent_value('relationship') // 10
    # 心情
    if isinstance(target, ShipGirl):
        happiness_source *= (10 + 2 * target.get_mood()) / 10
    # TODO: 媚药
    # TODO: 利尿剂

    # 因为没看懂tw这段逻辑是何意味 所以暂时注释掉
    # # 旁人在场+情绪
    # if (NpcManager.with_mob(target.location['region'], target.location['node'])
    #     and target.base['emotion'] < MAX_EMOTION // 2):
    #     happiness_source *= 1.2

    # 约会中
    if isinstance(target, ShipGirl) and target.is_dating():
        happiness_source *= 1.3
    # abl: 亲密
    happiness_source *= (100 + 5 * target.abl['intimacy_abl']) // 100
    # abl: 欲望
    happiness_source *= (100 + 5 * target.abl['desire_abl']) // 100
    # 好感度
    if isinstance(target, ShipGirl):
        if target.favor <= 10:
            happiness_source *= 0.5
        elif target.favor <= 50:
            happiness_source *= 0.8
        elif target.favor <= 100:
            happiness_source *= 1.0
        elif target.favor <= 300:
            happiness_source *= 1.2
        elif target.favor <= 500:
            happiness_source *= 1.2
        elif target.favor <= 700:
            happiness_source *= 1.3
        elif target.favor <= 1000:
            happiness_source *= 1.4
        elif target.favor <= 3000:
            happiness_source *= 1.5
        elif target.favor <= 5000:
            happiness_source *= 1.7
        elif target.favor <= 500_000:
            happiness_source = min(1_000_000_000, happiness_source * (100 + target.favor / 50) / 100)

    return {
        'kindness_palam': {'chara': 'target', 'value': int(happiness_source)},
        'lust_palam': {'chara': 'source', 'value': int(happiness_source / 10)}
    }


def conquest_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理conquest_source
        return: target优越 TODO: target欲情 player屈服 target羞耻"""
    conquest_source = source.get('conquest_source', 0)
    # TODO: 地位分歧 高位和低位
    # TODO: 对方主导
    match target.abl['sadism_abl']:
        case 0:
            conquest_source *= 0.7
        case 1:
            pass
        case 2:
            conquest_source *= 1.3
        case 3:
            conquest_source *= 1.7
        case 4:
            conquest_source *= 2.0
        case _:
            conquest_source *= (175 + target.abl['sadism_abl'] * 15) / 100

    # target优越 TODO: target欲情 player屈服 target羞耻(需要地位分歧)
    return {
        'superiority_palam': {'chara': 'target', 'value': int(conquest_source)},
    }


def passivity_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理passivity_source
        return: target好意 TODO: target屈服 player恭顺 target恭顺"""
    passivity_source = source.get('passivity_source', 0)
    # TODO: 地位分歧 高位和低位
    # TODO: 对方主导
    # abl: 亲密
    passivity_source *= (70 + 10 * target.abl['intimacy_abl']) // 100

    # target好意 TODO: target屈服 player恭顺 target恭顺(需要地位分歧)
    return {
        'kindness_palam': {'chara': 'target', 'value': int(passivity_source)},
    }


def unclean_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理unclean_source
        return: 不快"""
    unclean_source = source.get('unclean_source', 0)
    # abl: 顺从
    match target.abl['obedience_abl']:
        case 0:
            unclean_source *= 1.5
        case 1 | 2 | 3:
            unclean_source *= 1.3
        case 4 | 5 | 6:
            pass
        case 7 | 8 | 9:
            unclean_source *= 0.75
        case 10 | 11 | 12:
            unclean_source *= 0.5
        case 13 | 14 | 15:
            unclean_source *= 0.25
        case _:
            unclean_source *= 0.1
    # TODO: 心智魔方
    return {
        'disgust_palam': {'chara': 'target', 'value': int(unclean_source)}
    }


def depression_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理depression_source
        return: 抑郁"""
    depression_source = source.get('depression_source', 0)
    # 心情
    if isinstance(target, ShipGirl):
        depression_source *= (10 - 2 * target.get_mood()) / 10
    # 陷落素质
    if target.get_talent_value('relationship') == 1:
        depression_source *= 0.75
    elif target.get_talent_value('relationship') >= 2:
        depression_source *= 0.25
    # abl: 顺从
    match target.abl['obedience_abl']:
        case 0:
            depression_source *= 1.5
        case 1 | 2 | 3:
            depression_source *= 1.3
        case 4 | 5 | 6:
            pass
        case 7 | 8 | 9:
            depression_source *= 0.75
        case 10 | 11 | 12:
            depression_source *= 0.5
        case 13 | 14 | 15:
            depression_source *= 0.25
        case _:
            depression_source *= 0.1
    # abl: 欲望
    match target.abl['desire_abl']:
        case 0:
            depression_source *= 2.0
        case 1 | 2 | 3:
            depression_source *= 1.5
        case 4 | 5 | 6:
            pass
        case 7 | 8 | 9:
            depression_source *= 0.75
        case 10 | 11 | 12:
            depression_source *= 0.5
        case 13 | 14 | 15:
            depression_source *= 0.25
        case _:
            depression_source *= 0.1
    # TODO: 心智魔方
    return {
        'depression_palam': {'chara': 'target', 'value': int(depression_source)}
    }


def escape_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理escape_source
        return: 反感"""
    escape_source = source.get('escape_source', 0)
    # 性的兴趣
    if target.get_talent_value('sexual_interest') > 0:
        escape_source *= 0.8
    elif target.get_talent_value('sexual_interest') < 0:
        escape_source *= 2.0
    # abl: 顺从
    match target.abl['obedience_abl']:
        case 0:
            escape_source *= 1.5
        case 1 | 2 | 3:
            escape_source *= 1.3
        case 4 | 5 | 6:
            pass
        case 7 | 8 | 9:
            escape_source *= 0.75
        case 10 | 11 | 12:
            escape_source *= 0.5
        case 13 | 14 | 15:
            escape_source *= 0.25
        case _:
            escape_source *= 0.1
    # abl: 受虐属性
    match target.abl['masochistic_abl']:
        case 0:
            pass
        case 1 | 2 | 3:
            escape_source *= 0.9
        case 4 | 5:
            escape_source *= 0.75
        case 6 | 7:
            escape_source *= 0.6
        case 8 | 9:
            escape_source *= 0.5
        case 10 | 11 | 12:
            escape_source *= 0.3
        case 13 | 14 | 15:
            escape_source *= 0.2
        case _:
            escape_source *= 0.1
    # TODO: 心智魔方
    return {
        'disgust_palam': {'chara': 'target', 'value': int(escape_source)}
    }


def disgust_source(source: dict[str, int], target: Character) -> dict[str, dict[str, str | int]]:
    """处理disgust_source
        return: 反感"""
    disgust_source = source.get('disgust_source', 0)
    # 心情
    if isinstance(target, ShipGirl):
        disgust_source *= (10 - 3 * target.get_mood()) / 10
    # TODO: 对方主导
    # abl: 顺从
    match target.abl['obedience_abl'] + target.abl['intimacy_abl']:
        case 0:
            disgust_source *= 2.0
        case 1 | 2 | 3:
            disgust_source *= 1.25
        case 4 | 5 | 6 | 7:
            pass
        case 8 | 9 | 10:
            disgust_source *= 0.75
        case 11 | 12 | 13 | 14:
            disgust_source *= 0.5
        case 15 | 16 | 17 | 18 | 19:
            disgust_source *= 0.25
        case 20 | 21 | 22 | 23 | 24:
            disgust_source *= 0.1
        case _:
            disgust_source *= 0.05
    # abl: 侍奉精神
    match target.abl['servant_abl']:
        case 0:
            pass
        case 1 | 2 | 3:
            disgust_source *= 0.9
        case 4 | 5:
            disgust_source *= 0.75
        case 6 | 7:
            disgust_source *= 0.6
        case 8 | 9:
            disgust_source *= 0.5
        case 10 | 11 | 12:
            disgust_source *= 0.3
        case 13 | 14 | 15:
            disgust_source *= 0.2
        case _:
            disgust_source *= 0.1
    # abl: 受虐属性
    match target.abl['masochistic_abl']:
        case 0:
            pass
        case 1 | 2 | 3:
            disgust_source *= 0.9
        case 4 | 5:
            disgust_source *= 0.75
        case 6 | 7:
            disgust_source *= 0.6
        case 8 | 9:
            disgust_source *= 0.5
        case 10 | 11 | 12:
            disgust_source *= 0.3
        case 13 | 14 | 15:
            disgust_source *= 0.2
        case _:
            disgust_source *= 0.1
    # TODO: 心智魔方
    return {
        'disgust_palam': {'chara': 'target', 'value': int(disgust_source)}
    }


def abl_revision(source: int | float, abl: int, abl_type: bool):
    """处理abl对source的修正"""
    modifier1 = {
        0: 0.1,
        1: 0.3,
        2: 0.5,
        3: 1.0,
        4: 1.5,
        5: 2.0,
        6: 2.5,
        7: 3.0,
        8: 3.5,
        9: 4.0,
        10: 5.0,
    }
    modifier2 = {
        0: 0.2,
        1: 0.4,
        2: 0.8,
        3: 1.2,
        4: 1.6,
        5: 2.0,
        6: 2.4,
        7: 2.8,
        8: 3.2,
        9: 3.6,
    }
    if abl_type:
        return source * modifier1.get(abl, 6.0)
    else:
        return source * modifier2.get(abl, 5.0)


def p_source_revision(abl: int, is_sen: bool):
    """处理abl对快感系source的修正"""
    if is_sen:
        if 0 <= abl <= 5:
            return 10 + 7 * abl
        elif 5 < abl <= 9:
            return 25 + 4 * abl
        elif 9 < abl <= 15:
            return 45 + 2 * abl
        elif 15 < abl <= 19:
            return 70 + abl
        else:
            return 90
    else:
        if 0 <= abl <= 5:
            return 25 + 7 * abl
        elif 5 < abl <= 9:
            return 45 + 3 * abl
        elif 9 < abl <= 15:
            return 60 + 2 * abl
        elif 15 < abl <= 19:
            return 80 + abl
        else:
            return 100
