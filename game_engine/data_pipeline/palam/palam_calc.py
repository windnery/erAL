from config.mood_enum import Mood
from config.attr_defs import ATTR_DEFS
from game_engine.models.character import Character
from game_engine.models.shipgirl import ShipGirl

def palam_calc(src: dict[str, int], source: Character, target: Character):
    """将source转成palam"""
    mes_source: list[str] = [f'{source.name}']
    mes_target: list[str] = [f'{target.name}']

    palam_dict_list: list[dict[str, dict[str, str|int]]] = []
    palam_dict_list.append(love_source(src, target))  # type: ignore
    palam_dict_list.append(sex_act_source(src, target))  # type: ignore
    palam_dict_list.append(achievement_source(src, target))  # type: ignore
    palam_dict_list.append(pain_source(src, target))  # type: ignore
    palam_dict_list.append(fear_source(src, target))  # type: ignore
    palam_dict_list.append(lubrication_source(src, target))  # type: ignore
    palam_dict_list.append(lust_source(src, target))  # type: ignore
    palam_dict_list.append(obedience_source(src, target))  # type: ignore
    palam_dict_list.append(exposure_source(src, target))  # type: ignore
    palam_dict_list.append(submission_source(src, target))  # type: ignore
    palam_dict_list.append(happiness_source(src, target))  # type: ignore
    palam_dict_list.append(conquest_source(src, target))  # type: ignore
    palam_dict_list.append(passivity_source(src, target))  # type: ignore
    palam_dict_list.append(unclean_source(src, target))  # type: ignore
    palam_dict_list.append(depression_source(src, target))  # type: ignore
    palam_dict_list.append(escape_source(src, target))  # type: ignore
    palam_dict_list.append(disgust_source(src, target))  # type: ignore

    # 聚合：按 (chara, palam) 求和
    merged: dict[tuple[str, str], int] = {}
    for palam_dict in palam_dict_list:
        for palam, info in palam_dict.items():
            key = (info['chara'], palam)          # ('target', 'lust_palam')
            merged[key] = merged.get(key, 0) + int(info['value']) # type: ignore

    # 统一应用 + 打印
    for (chara_kind, palam), value in merged.items():
        if value == 0:
            continue
        chara = source if chara_kind == 'source' else target
        mes = f'{ATTR_DEFS["palam"][palam]["name"]} {chara.palam[palam]} + {value} = {chara.palam[palam] + value}'
        (mes_source if chara_kind == 'source' else mes_target).append(mes)
        chara.palam[palam] += value

    return mes_source, mes_target



def love_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理love_source
        return: 恭顺 欲情"""
    # TODO: 强行
    love_source = source.get('love_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    love_source_1 = abl_revision(love_source, target_chara.abl['obedience_abl'], True)
    # abl: 欲望
    love_source_2 = abl_revision(love_source, target_chara.abl['desire_abl'], False)
    return {
        'obedience_palam': {'chara': 'target', 'value': int(love_source_1)},
        'lust_palam': {'chara': 'target', 'value': int(love_source_2)}
    }

def sex_act_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理sex_act_source
        return: 习得"""
    sex_act_source = source.get('sex_act_source', 0)
    # TODO: 对方主导
    # abl: 技巧
    sex_act_source = abl_revision(sex_act_source, target_chara.abl['skill_abl'], True)
    # abl: 侍奉精神
    match target_chara.abl['servant_abl']:
        case 0: sex_act_source *= 0.6
        case 1: sex_act_source *= 0.8
        case 2: sex_act_source *= 1.0
        case 3: sex_act_source *= 1.2
        case 4: sex_act_source *= 1.4
        case 5: sex_act_source *= 1.7
        case 6: sex_act_source *= 2.0
        case 7: sex_act_source *= 2.4
        case 8: sex_act_source *= 2.8
        case 9: sex_act_source *= 4.0
        case _: sex_act_source *= 5.0
    return {
        'learn_palam': {'chara': 'target', 'value': int(sex_act_source)}
    }

def achievement_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理achievement_source
        return: 恭顺"""
    achievement_source = source.get('achievement_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    achievement_source = abl_revision(achievement_source, target_chara.abl['obedience_abl'], True)
    # abl: 侍奉精神
    achievement_source = abl_revision(achievement_source, target_chara.abl['servant_abl'], False)
    return {
        'obedience_palam': {'chara': 'target', 'value': int(achievement_source)}
    }

def pain_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理pain_source
        return: 苦痛 欲情 恐惧"""
    pain_source2pain = source.get('pain_source', 0)
    pain_source2lust = source.get('pain_source', 0)
    pain_source2fear = source.get('pain_source', 0) // 20

    # abl: 受虐属性
    match target_chara.abl['masochistic_abl']:
        case 0: pain_source2lust = 0
        case 1: pain_source2lust *= 0.1
        case 2: pain_source2lust *= 0.2
        case 3: pain_source2lust *= 0.3
        case 4: pain_source2lust *= 0.45
        case 5: pain_source2lust *= 0.6
        case 6: pain_source2lust *= 0.75
        case 7: pain_source2lust *= 0.9
        case 8: pain_source2lust *= 1.2
        case 9: pain_source2lust *= 1.5
        case _: pain_source2lust *= 3.0
    # TODO: 体型
    # TODO: 调教者施虐狂
    # TODO: 胆怯
    return {
        'pain_palam': {'chara': 'target', 'value': int(pain_source2pain)},
        'lust_palam': {'chara': 'target', 'value': int(pain_source2lust)},
        'fear_palam': {'chara': 'target', 'value': int(pain_source2fear)}
    }
def fear_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理fear_source
        return: 恐惧"""
    fear_source = source.get('fear_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    fear_source = abl_revision(fear_source, target_chara.abl['obedience_abl'], True)
    return {
        'fear_palam': {'chara': 'target', 'value': int(fear_source)}
    }

def lubrication_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理lubrication_source
        return: 润滑"""
    lubrication_source = source.get('lubrication_source', 0)
    # TODO: 体型
    return {
        'lubrication_palam': {'chara': 'target', 'value': int(lubrication_source)}
    }

def lust_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理lust_source
        return: 欲情"""
    lust_source = source.get('lust_source', 0)
    # TODO: 发情
    # abl: 欲望
    lust_source = abl_revision(lust_source, target_chara.abl['desire_abl'], False)
    return {
        'lust_palam': {'chara': 'target', 'value': int(lust_source)}
    }

def obedience_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理obedience_source
        return: 恭顺"""
    obedience_source = source.get('obedience_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    match target_chara.abl['obedience_abl']:
        case 0: obedience_source *= 0.5
        case 1: obedience_source *= 0.8
        case 2: obedience_source *= 1.0
        case 3: obedience_source *= 1.2
        case 4: obedience_source *= 1.4
        case 5: obedience_source *= 1.6
        case 6: obedience_source *= 1.8
        case 7: obedience_source *= 2.0
        case 8: obedience_source *= 2.4
        case 9: obedience_source *= 3.0
        case _: obedience_source *= 5.0
    return {
        'obedience_palam': {'chara': 'target', 'value': int(obedience_source)}
    }

def exposure_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理exposure_source
        return: 欲情 羞耻"""
    exposure_source_1 = source.get('exposure_source', 0)
    exposure_source_2 = source.get('exposure_source', 0)
    # TODO: 害羞和不知羞耻
    # 润滑追加露出
    exposure_source_1 += source.get('lubrication_source', 0) // 2
    # TODO: 对方主导
    # abl: 露出癖
    match target_chara.abl['exposure_abl']:
        case 0: exposure_source_1 = 0
        case 1: exposure_source_1 *= 0.1
        case 2: exposure_source_1 *= 0.2
        case 3: exposure_source_1 *= 0.4
        case 4: exposure_source_1 *= 0.6
        case 5: exposure_source_1 *= 0.8
        case 6: exposure_source_1 *= 1.0
        case 7: exposure_source_1 *= 1.2
        case 8: exposure_source_1 *= 1.4
        case 9: exposure_source_1 *= 1.6
        case _: exposure_source_1 *= 2.0
    # 羞耻追加
    if target_chara.palam_lv['shame_palam'] < 1:
        pass
    elif target_chara.palam_lv['shame_palam'] < 2:
        exposure_source_2 *= 0.9
    elif target_chara.palam_lv['shame_palam'] < 3:
        exposure_source_2 *= 0.8
    elif target_chara.palam_lv['shame_palam'] < 4:
        exposure_source_2 *= 0.7
    else:
        exposure_source_2 *= 0.6

    return {
        'lust_palam': {'chara': 'target', 'value': int(exposure_source_1)},
        'shame_palam': {'chara': 'target', 'value': int(exposure_source_2)}
    }
def submission_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理submission_source
        return: 屈服"""
    submission_source = source.get('submission_source', 0)
    # TODO: 对方主导
    # abl: 顺从
    submission_source = abl_revision(submission_source, target_chara.abl['obedience_abl'], True)
    # abl: 侍奉精神
    match target_chara.abl['servant_abl']:
        case 0: pass
        case 1: submission_source *= 1.5
        case 2: submission_source *= 2.0
        case 3: submission_source *= 2.5
        case 4: submission_source *= 3.0
        case 5: submission_source *= 3.5
        case 6: submission_source *= 4.0
        case 7: submission_source *= 4.5
        case 8: submission_source *= 5.0
        case 9: submission_source *= 5.5
        case _: submission_source *= 7.0
    return {
        'submission_palam': {'chara': 'target', 'value': int(submission_source)}
    }
def happiness_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理happiness_source
        return: target好意 player欲情"""
    happiness_source = source.get('happiness_source', 0)
    # TODO: 对方主导
    # TODO: 陷落素质
    # 心情
    happiness_source *= (10 + 2 * get_mood_revision(target_chara.get_mood())) / 10
    # TODO: 媚药
    # TODO: 利尿剂
    # TODO: 情绪
    # TODO: 约会中
    # abl: 亲密
    happiness_source *= (100 + 5 * target_chara.abl['intimacy_abl']) // 100
    # abl: 欲望
    happiness_source *= (100 + 5 * target_chara.abl['desire_abl']) // 100
    # 好感度
    if target_chara.favor <= 10:
        happiness_source *= 0.5
    elif target_chara.favor <= 50:
        happiness_source *= 0.8
    elif target_chara.favor <= 100:
        happiness_source *= 1.0
    elif target_chara.favor <= 300:
        happiness_source *= 1.2
    elif target_chara.favor <= 500:
        happiness_source *= 1.2
    elif target_chara.favor <= 700:
        happiness_source *= 1.3
    elif target_chara.favor <= 1000:
        happiness_source *= 1.4
    elif target_chara.favor <= 3000:
        happiness_source *= 1.5
    elif target_chara.favor <= 5000:
        happiness_source *= 1.7
    elif target_chara.favor <= 500_000:
        happiness_source = min(1_000_000_000, happiness_source * (100 + target_chara.favor / 50) / 100)

    return {
        'kindness_palam': {'chara': 'target', 'value': int(happiness_source)},
        'lust_palam': {'chara': 'source', 'value': int(happiness_source / 10)}
    }

def conquest_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理conquest_source
        return: target优越 TODO: target欲情 player屈服 target羞耻"""
    conquest_source = source.get('conquest_source', 0)
    # TODO: 地位分歧 高位和低位
    # TODO: 对方主导
    match target_chara.abl['sadism_abl']:
        case 0: conquest_source *= 0.7
        case 1: pass
        case 2: conquest_source *= 1.3
        case 3: conquest_source *= 1.7
        case 4: conquest_source *= 2.0
        case _: conquest_source *= (175 + target_chara.abl['sadism_abl'] * 15) / 100

    # target优越 TODO: target欲情 player屈服 target羞耻(需要地位分歧)
    return {
        'superiority_palam': {'chara': 'target', 'value': int(conquest_source)},
    }

def passivity_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理passivity_source
        return: target好意 TODO: target屈服 player恭顺 target恭顺"""
    passivity_source = source.get('passivity_source', 0)
    # TODO: 地位分歧 高位和低位
    # TODO: 对方主导
    # abl: 亲密
    passivity_source *= (70 + 10 * target_chara.abl['intimacy_abl']) // 100

    # target好意 TODO: target屈服 player恭顺 target恭顺(需要地位分歧)
    return {
        'kindness_palam': {'chara': 'target', 'value': int(passivity_source)},
    }

def unclean_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理unclean_source
        return: 不快"""
    unclean_source = source.get('unclean_source', 0)
    # abl: 顺从
    match target_chara.abl['obedience_abl']:
        case 0: unclean_source *= 1.5
        case 1|2|3: unclean_source *= 1.3
        case 4|5|6: pass
        case 7|8|9: unclean_source *= 0.75
        case 10|11|12: unclean_source *= 0.5
        case 13|14|15: unclean_source *= 0.25
        case _: unclean_source *= 0.1
    # TODO: 心智魔方
    return {
        'disgust_palam': {'chara': 'target', 'value': int(unclean_source)}
    }

def depression_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理depression_source
        return: 抑郁"""
    depression_source = source.get('depression_source', 0)
    # 心情
    depression_source *= (10 + 2 * get_mood_revision(target_chara.get_mood())) / 10
    # TODO: 陷落素质
    # abl: 顺从
    match target_chara.abl['obedience_abl']:
        case 0: depression_source *= 1.5
        case 1|2|3: depression_source *= 1.3
        case 4|5|6: pass
        case 7|8|9: depression_source *= 0.75
        case 10|11|12: depression_source *= 0.5
        case 13|14|15: depression_source *= 0.25
        case _: depression_source *= 0.1
    # abl: 欲望
    match target_chara.abl['desire_abl']:
        case 0: depression_source *= 2.0
        case 1|2|3: depression_source *= 1.5
        case 4|5|6: pass
        case 7|8|9: depression_source *= 0.75
        case 10|11|12: depression_source *= 0.5
        case 13|14|15: depression_source *= 0.25
        case _: depression_source *= 0.1
    # TODO: 心智魔方
    return {
        'depression_palam': {'chara': 'target', 'value': int(depression_source)}
    }

def escape_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理escape_source
        return: 反感"""
    escape_source = source.get('escape_source', 0)
    # TODO: 性的兴趣
    # abl: 顺从
    match target_chara.abl['obedience_abl']:
        case 0: escape_source *= 1.5
        case 1|2|3: escape_source *= 1.3
        case 4|5|6: pass
        case 7|8|9: escape_source *= 0.75
        case 10|11|12: escape_source *= 0.5
        case 13|14|15: escape_source *= 0.25
        case _: escape_source *= 0.1
    # abl: 受虐属性
    match target_chara.abl['masochistic_abl']:
        case 0: pass
        case 1|2|3: escape_source *= 0.9
        case 4|5: escape_source *= 0.75
        case 6|7: escape_source *= 0.6
        case 8|9: escape_source *= 0.5
        case 10|11|12: escape_source *= 0.3
        case 13|14|15: escape_source *= 0.2
        case _: escape_source *= 0.1
    # TODO: 心智魔方
    return {
        'disgust_palam': {'chara': 'target', 'value': int(escape_source)}
    }

def disgust_source(source: dict[str, int], target_chara: ShipGirl) -> dict[str, dict[str, str|int]]:
    """处理disgust_source
        return: 反感"""
    disgust_source = source.get('disgust_source', 0)
    # 心情
    disgust_source *= (10 - 3 * get_mood_revision(target_chara.get_mood())) / 10
    # TODO: 对方主导
    # abl: 顺从
    match target_chara.abl['obedience_abl'] + target_chara.abl['intimacy_abl']:
        case 0: disgust_source *= 2.0
        case 1|2|3: disgust_source *= 1.25
        case 4|5|6|7: pass
        case 8|9|10: disgust_source *= 0.75
        case 11|12|13|14: disgust_source *= 0.5
        case 15|16|17|18|19: disgust_source *= 0.25
        case 20|21|22|23|24: disgust_source *= 0.1
        case _: disgust_source *= 0.05
    # abl: 侍奉精神
    match target_chara.abl['servant_abl']:
        case 0: pass
        case 1|2|3: disgust_source *= 0.9
        case 4|5: disgust_source *= 0.75
        case 6|7: disgust_source *= 0.6
        case 8|9: disgust_source *= 0.5
        case 10|11|12: disgust_source *= 0.3
        case 13|14|15: disgust_source *= 0.2
        case _: disgust_source *= 0.1
    # abl: 受虐属性
    match target_chara.abl['masochistic_abl']:
        case 0: pass
        case 1|2|3: disgust_source *= 0.9
        case 4|5: disgust_source *= 0.75
        case 6|7: disgust_source *= 0.6
        case 8|9: disgust_source *= 0.5
        case 10|11|12: disgust_source *= 0.3
        case 13|14|15: disgust_source *= 0.2
        case _: disgust_source *= 0.1
    # TODO: 心智魔方
    return {
        'disgust_palam': {'chara': 'target', 'value': int(disgust_source)}
    }



def abl_revision(source: int|float, abl: int, type: bool):
    """处理abl对source的修正"""
    if type:
        match abl:
            case 0:
                return source * 0.1
            case 1:
                return source * 0.3
            case 2:
                return source * 0.5
            case 3:
                return source * 1.0
            case 4:
                return source * 1.5
            case 5:
                return source * 2.0
            case 6:
                return source * 2.5
            case 7:
                return source * 3.0
            case 8:
                return source * 3.5
            case 9:
                return source * 4.0
            case 10:
                return source * 5.0
            case _:
                return source * 6.0
    else:
        match abl:
            case 0:
                return source * 0.2
            case 1:
                return source * 0.4
            case 2:
                return source * 0.8
            case 3:
                return source * 1.2
            case 4:
                return source * 1.6
            case 5:
                return source * 2.0
            case 6:
                return source * 2.4
            case 7:
                return source * 2.8
            case 8:
                return source * 3.2
            case 9:
                return source * 3.6
            case _:
                return source * 5.0
            
def get_mood_revision(mood: Mood):
    """处理mood对source的修正"""
    match mood:
        case Mood.ANGRY:
            return -1.5
        case Mood.UNHAPPY:
            return -1.0
        case Mood.NEUTRAL:
            return 1.0
        case Mood.HAPPY:
            return 1.5
        case Mood.DELIGHTED:
            return 2.0
        case Mood.BLISS:
            return 2.5