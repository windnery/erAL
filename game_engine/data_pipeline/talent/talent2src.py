from config.source_config import ALL_SOURCE_KEYS, POSITIVE_SRC, NEGATIVE_SRC
from config.talent_config import TALENT2SRC_SET
from game_engine.models.character import Character


def talent2src(chara: Character, source: dict[str, int | float]):
    """天赋对source的修正"""
    for k, v in chara.talent.items():
        if k in TALENT2SRC_SET:
            func_name = f'_{k}2src'
            func = globals().get(func_name)
            if func:
                if k in ['relationship', 'courage', 'attitude', 'response', 'self_respect', 'sexual_interest',
                         'sense_of_shame', 'pain_tolerance', 'wetness', 'foul_tolerance', 'pleasure_response',
                         'c_sensitivity', 'v_sensitivity', 'a_sensitivity', 'b_sensitivity', 'm_sensitivity',
                         'bra_size', 'hip_size']:
                    func(v, source)
                elif k == 'tsundere':
                    intimacy_abl = chara.abl.get('intimacy_abl', 0)
                    func(source, intimacy_abl)
                else:
                    func(source)


def _virgin2src(source: dict[str, int | float]):
    """处女对source的修正"""
    source['sex_act_source'] *= 0.8
    source['exposure_source'] *= 1.2
    source['escape_source'] *= 1.2


def _relationship2src(flag: str, source: dict[str, int | float]):
    """陷落阶段对source的修正"""
    if flag == '0':
        # 陌生
        for p in POSITIVE_SRC:
            source[p] *= 0.8
        for n in NEGATIVE_SRC:
            source[n] *= 1.2
    elif flag == '1':
        # 友好
        for p in POSITIVE_SRC:
            source[p] *= 1.2
        for n in NEGATIVE_SRC:
            source[n] *= 0.8
    elif flag == '2':
        # 喜欢
        for p in POSITIVE_SRC:
            source[p] *= 1.5
        for n in NEGATIVE_SRC:
            source[n] *= 0.6
    elif flag == '3':
        # 爱
        for p in POSITIVE_SRC:
            source[p] *= 2.0
        for n in NEGATIVE_SRC:
            source[n] *= 0.4
    else:
        # 誓约
        for p in POSITIVE_SRC:
            source[p] *= 3.0
        for n in NEGATIVE_SRC:
            source[n] *= 0.1


def _lover2src(source: dict[str, int | float]):
    """恋人对source的修正"""
    for p in POSITIVE_SRC:
        source[p] *= 1.5
    for n in NEGATIVE_SRC:
        source[n] *= 0.7


def _courage2src(flag: str, source: dict[str, int | float]):
    """胆量对source的修正"""
    if flag == '-1':
        # 胆怯
        source['pain_source'] *= 1.2
        source['fear_source'] *= 1.2
        source['escape_source'] *= 1.2
        source['obedience_source'] *= 1.2
        source['submission_source'] *= 1.2
        source['conquest_source'] *= 1.2
        source['passivity_source'] *= 1.2
    elif flag == '1':
        # 坚强
        source['pain_source'] *= 0.8
        source['fear_source'] *= 0.8
        source['escape_source'] *= 0.8
        source['obedience_source'] *= 0.8
        source['submission_source'] *= 0.8
        source['conquest_source'] *= 0.8
        source['passivity_source'] *= 0.8


def _attitude2src(flag: str, source: dict[str, int | float]):
    """态度对source的修正"""
    if flag == '-1':
        # 坦率
        source['achievement_source'] *= 1.2
        source['lust_source'] *= 1.2
        source['obedience_source'] *= 1.2
        source['submission_source'] *= 1.1
        source['conquest_source'] *= 1.1
        source['passivity_source'] *= 1.1
        source['escape_source'] *= 0.9
    elif flag == '1':
        # 叛逆
        for p in POSITIVE_SRC:
            source[p] *= 0.9
        for n in NEGATIVE_SRC:
            source[n] *= 1.1


def _response2src(flag: str, source: dict[str, int | float]):
    """应答对source的修正"""
    if flag == '-1':
        # 老实
        source['obedience_source'] *= 1.2
        source['conquest_source'] *= 1.2
        source['passivity_source'] *= 1.2
    elif flag == '1':
        # 傲慢
        source['obedience_source'] *= 0.8
        source['conquest_source'] *= 0.8
        source['passivity_source'] *= 0.8
        source['escape_source'] *= 0.8
        source['submission_source'] *= 0.8
        source['achievement_source'] *= 0.8
        source['disgust_source'] *= 1.2


def _self_respect2src(flag: str, source: dict[str, int | float]):
    """自尊心对source的修正"""
    if flag == '-1':
        # 自尊心低
        source['achievement_source'] *= 1.2
        source['obedience_source'] *= 1.2
        source['submission_source'] *= 1.2
        source['conquest_source'] *= 1.2
        source['depression_source'] *= 1.1
        source['passivity_source'] *= 1.2
    elif flag == '1':
        # 自尊心高
        source['achievement_source'] *= 0.8
        source['obedience_source'] *= 0.8
        source['submission_source'] *= 0.8
        source['conquest_source'] *= 0.8
        source['passivity_source'] *= 0.8
        source['pain_source'] *= 0.9
        source['depression_source'] *= 0.9
        source['fear_source'] *= 0.9
        source['escape_source'] *= 0.9


def _tsundere2src(source: dict[str, int | float], intimacy_abl: int):
    """傲娇对source的修正"""
    if intimacy_abl <= 4:
        # 亲密低
        source['obedience_source'] *= 0.7
        source['submission_source'] *= 0.7
        source['conquest_source'] *= 0.7
        source['passivity_source'] *= 0.7
    else:
        # 亲密高时反转
        for p in POSITIVE_SRC:
            source[p] *= 1.2
        for n in NEGATIVE_SRC:
            source[n] *= 0.8


def _self_control2src(source: dict[str, int | float]):
    """自制力对source的修正"""
    source['exposure_source'] *= 0.8
    source['lust_source'] *= 0.8
    source['depression_source'] *= 0.9


def _indifference2src(source: dict[str, int | float]):
    """冷淡对source的修正"""
    for p in POSITIVE_SRC:
        source[p] *= 0.9


def _emotional_deficiency2src(source: dict[str, int | float]):
    """感情缺乏对source的修正"""
    for k in ALL_SOURCE_KEYS:
        source[k] *= 0.9


def _sexual_interest2src(flag: str, source: dict[str, int | float]):
    """性的兴趣对source的修正"""
    if flag == '-1':
        # 保守的
        source['sex_act_source'] *= 0.8
        source['lust_source'] *= 0.8
        source['exposure_source'] *= 0.8
        source['c_pleasure_source'] *= 0.8
        source['v_pleasure_source'] *= 0.8
        source['a_pleasure_source'] *= 0.8
        source['b_pleasure_source'] *= 0.8
        source['m_pleasure_source'] *= 0.8
        source['lubrication_source'] *= 0.8
    elif flag == '1':
        # 好奇心
        source['sex_act_source'] *= 1.2
        source['lust_source'] *= 1.2
        source['exposure_source'] *= 1.2
        source['c_pleasure_source'] *= 1.2
        source['v_pleasure_source'] *= 1.2
        source['a_pleasure_source'] *= 1.2
        source['b_pleasure_source'] *= 1.2
        source['m_pleasure_source'] *= 1.2
        source['lubrication_source'] *= 1.2


def _bright2src(source: dict[str, int | float]):
    """开朗对source的修正"""
    source['happiness_source'] *= 1.2
    source['lust_source'] *= 1.2
    source['love_source'] *= 1.2
    source['exposure_source'] *= 1.1
    source['passivity_source'] *= 0.8
    source['depression_source'] *= 0.8
    source['escape_source'] *= 0.9


def _morose2src(source: dict[str, int | float]):
    """阴郁对source的修正"""
    source['happiness_source'] *= 0.8
    source['lust_source'] *= 0.8
    source['love_source'] *= 0.8
    source['exposure_source'] *= 0.9
    source['passivity_source'] *= 1.2
    source['depression_source'] *= 1.2
    source['escape_source'] *= 1.1
    source['sex_act_source'] *= 0.9


def _impassable_line2src(source: dict[str, int | float]):
    """难以逾越的底线对source的修正"""
    # 非处女会移除
    source['sex_act_source'] *= 0.5
    source['achievement_source'] *= 0.5
    source['lust_source'] *= 0.5
    source['disgust_source'] *= 1.2


def _not_minding_the_gaze2src(source: dict[str, int | float]):
    """不在意他人目光对source的修正"""
    source['exposure_source'] *= 1.5
    source['unclean_source'] *= 0.8


def _innocent2src(source: dict[str, int | float]):
    """天真对source的修正"""
    source['sex_act_source'] *= 0.8
    source['lust_source'] *= 0.8
    source['love_source'] *= 0.8
    source['obedience_source'] *= 1.2
    source['submission_source'] *= 1.2
    source['achievement_source'] *= 1.2

    for k in NEGATIVE_SRC:
        source[k] *= 1.2


def _chastity2src(flag: str, source: dict[str, int | float]):
    """贞操对source的修正"""
    if flag == '-1':
        # 不在乎贞操
        source['sex_act_source'] *= 1.5
        source['lust_source'] *= 1.2
        source['achievement_source'] *= 1.2
        source['lubrication_source'] *= 1.2
    elif flag == '1':
        # 贞操重视
        source['sex_act_source'] *= 0.5
        source['lust_source'] *= 0.8
        source['achievement_source'] *= 0.8
        source['lubrication_source'] *= 0.8


def _self_love2src(flag: str, source: dict[str, int | float]):
    """自己爱对source的修正"""
    if flag == '-1':
        # 压抑
        source['sex_act_source'] *= 0.8
        source['lust_source'] *= 0.8
        source['exposure_source'] *= 0.8
        source['achievement_source'] *= 0.8
        source['c_pleasure_source'] *= 0.8
        source['v_pleasure_source'] *= 0.8
        source['a_pleasure_source'] *= 0.8
        source['b_pleasure_source'] *= 0.8
        source['m_pleasure_source'] *= 0.8
        source['lubrication_source'] *= 0.8
        source['conquest_source'] *= 1.2
        source['passivity_source'] *= 1.2
    elif flag == '1':
        # 解放
        source['sex_act_source'] *= 1.2
        source['lust_source'] *= 1.2
        source['exposure_source'] *= 1.2
        source['achievement_source'] *= 1.2
        source['c_pleasure_source'] *= 1.2
        source['v_pleasure_source'] *= 1.2
        source['a_pleasure_source'] *= 1.2
        source['b_pleasure_source'] *= 1.2
        source['m_pleasure_source'] *= 1.2
        source['lubrication_source'] *= 1.2
        source['conquest_source'] *= 0.8
        source['passivity_source'] *= 0.8


def _resistance2src(source: dict[str, int | float]):
    """抵抗对source的修正"""
    for k in POSITIVE_SRC:
        source[k] *= 0.9
    source['pain_source'] *= 0.9
    source['fear_source'] *= 0.9
    source['disgust_source'] *= 1.1
    source['escape_source'] *= 1.1


def _sense_of_shame2src(flag: str, source: dict[str, int | float]):
    """羞耻心对source的修正"""
    if flag == '-1':
        # 不知羞耻
        source['exposure_source'] *= 1.5
        source['unclean_source'] *= 0.8
        source['lubrication_source'] *= 1.2
        source['sex_act_source'] *= 1.2
        source['achievement_source'] *= 1.2
        source['lust_source'] *= 1.2
        source['passivity_source'] *= 0.8
    elif flag == '1':
        # 害羞
        source['exposure_source'] *= 0.5
        source['unclean_source'] *= 1.2
        source['lubrication_source'] *= 0.8
        source['sex_act_source'] *= 0.8
        source['achievement_source'] *= 0.8
        source['lust_source'] *= 0.8
        source['passivity_source'] *= 1.2


def _pain_tolerance2src(flag: str, source: dict[str, int | float]):
    """痛觉对source的修正"""
    if flag == '-1':
        # 不怕痛
        source['pain_source'] *= 1.3
    elif flag == '1':
        # 怕痛
        source['pain_source'] *= 0.7


def _wetness2src(flag: str, source: dict[str, int | float]):
    """易湿程度对source的修正"""
    if flag == '-1':
        # 不易湿
        source['lubrication_source'] *= 0.7
    elif flag == '1':
        # 容易湿
        source['lubrication_source'] *= 1.3


def _urophilia2src(source: dict[str, int | float]):
    """漏尿癖对source的修正"""
    source['lubrication_source'] *= 1.2


def _foul_tolerance2src(flag: str, source: dict[str, int | float]):
    """污臭耐性对source的修正"""
    if flag == '-2':
        # 洁癖
        source['unclean_source'] *= 2.0
    elif flag == '-1':
        # 污臭敏感
        source['unclean_source'] *= 1.5
    elif flag == '1':
        # 污臭钝感
        source['unclean_source'] *= 0.8
    elif flag == '2':
        # 污臭无视
        source['unclean_source'] *= 0.5


def _devoted2src(source: dict[str, int | float]):
    """献身的对source的修正"""
    source['obedience_source'] *= 1.2
    source['submission_source'] *= 1.2
    source['conquest_source'] *= 1.2
    source['passivity_source'] *= 1.2
    source['love_source'] *= 1.2
    source['lust_source'] *= 1.2
    source['sex_act_source'] *= 1.2
    source['achievement_source'] *= 1.2
    source['happiness_source'] *= 1.2
    source['escape_source'] *= 0.8


def _pleasure_response2src(flag: str, source: dict[str, int | float]):
    """快感应答对source的修正"""
    if flag == '-1':
        # 否定快感
        source['c_pleasure_source'] *= 0.8
        source['v_pleasure_source'] *= 0.8
        source['a_pleasure_source'] *= 0.8
        source['b_pleasure_source'] *= 0.8
        source['m_pleasure_source'] *= 0.8
    elif flag == '1':
        # 接受快感
        source['c_pleasure_source'] *= 1.2
        source['v_pleasure_source'] *= 1.2
        source['a_pleasure_source'] *= 1.2
        source['b_pleasure_source'] *= 1.2
        source['m_pleasure_source'] *= 1.2


def _vaginal_fan2src(source: dict[str, int | float]):
    """淫壶对source的修正"""
    source['c_pleasure_source'] *= 2.0
    source['v_pleasure_source'] *= 2.0


def _anal_fan2src(source: dict[str, int | float]):
    """淫尻对source的修正"""
    source['a_pleasure_source'] *= 2.0


def _breast_fan2src(source: dict[str, int | float]):
    """淫乳对source的修正"""
    source['b_pleasure_source'] *= 2.0


def _oral_fan2src(source: dict[str, int | float]):
    """淫舌对source的修正"""
    source['m_pleasure_source'] *= 2.0


def _c_sensitivity2src(flag: str, source: dict[str, int | float]):
    """C感度对source的修正"""
    if flag == '-1':
        # 钝感
        source['c_pleasure_source'] *= 0.7
    elif flag == '1':
        # 敏感
        source['c_pleasure_source'] *= 1.3
    elif flag == '2':
        # 过敏
        source['c_pleasure_source'] *= 1.6
    elif flag == '3':
        # 超敏
        source['c_pleasure_source'] *= 2.0
    elif flag == '4':
        # 极敏
        source['c_pleasure_source'] *= 2.5
    elif flag == '5':
        # 一触即溃
        source['c_pleasure_source'] *= 3.0


def _v_sensitivity2src(flag: str, source: dict[str, int | float]):
    """V感度对source的修正"""
    if flag == '-1':
        # 钝感
        source['v_pleasure_source'] *= 0.7
    elif flag == '1':
        # 敏感
        source['v_pleasure_source'] *= 1.3
    elif flag == '2':
        # 过敏
        source['v_pleasure_source'] *= 1.6
    elif flag == '3':
        # 超敏
        source['v_pleasure_source'] *= 2.0
    elif flag == '4':
        # 极敏
        source['v_pleasure_source'] *= 2.5
    elif flag == '5':
        # 一触即溃
        source['v_pleasure_source'] *= 3.0


def _a_sensitivity2src(flag: str, source: dict[str, int | float]):
    """A感度对source的修正"""
    if flag == '-1':
        # 钝感
        source['a_pleasure_source'] *= 0.7
    elif flag == '1':
        # 敏感
        source['a_pleasure_source'] *= 1.3
    elif flag == '2':
        # 过敏
        source['a_pleasure_source'] *= 1.6
    elif flag == '3':
        # 超敏
        source['a_pleasure_source'] *= 2.0
    elif flag == '4':
        # 极敏
        source['a_pleasure_source'] *= 2.5
    elif flag == '5':
        # 一触即溃
        source['a_pleasure_source'] *= 3.0


def _b_sensitivity2src(flag: str, source: dict[str, int | float]):
    """B感度对source的修正"""
    if flag == '-1':
        # 钝感
        source['b_pleasure_source'] *= 0.7
    elif flag == '1':
        # 敏感
        source['b_pleasure_source'] *= 1.3
    elif flag == '2':
        # 过敏
        source['b_pleasure_source'] *= 1.6
    elif flag == '3':
        # 超敏
        source['b_pleasure_source'] *= 2.0
    elif flag == '4':
        # 极敏
        source['b_pleasure_source'] *= 2.5
    elif flag == '5':
        # 一触即溃
        source['b_pleasure_source'] *= 3.0


def _m_sensitivity2src(flag: str, source: dict[str, int | float]):
    """M感度对source的修正"""
    if flag == '-1':
        # 钝感
        source['m_pleasure_source'] *= 0.7
    elif flag == '1':
        # 敏感
        source['m_pleasure_source'] *= 1.3
    elif flag == '2':
        # 过敏
        source['m_pleasure_source'] *= 1.6
    elif flag == '3':
        # 超敏
        source['m_pleasure_source'] *= 2.0
    elif flag == '4':
        # 极敏
        source['m_pleasure_source'] *= 2.5
    elif flag == '5':
        # 一触即溃
        source['m_pleasure_source'] *= 3.0


def _bra_size2src(flag: str, source: dict[str, int | float]):
    """胸围对source的修正"""
    if flag == '-2':
        # 绝壁
        source['b_pleasure_source'] *= 0.6
    elif flag == '-1':
        # 贫乳
        source['b_pleasure_source'] *= 0.8
    elif flag == '1':
        # 巨乳
        source['b_pleasure_source'] *= 1.2
    elif flag == '2':
        # 丰乳
        source['b_pleasure_source'] *= 1.5
    elif flag == '3':
        # 爆乳
        source['b_pleasure_source'] *= 2.0
    elif flag == '4':
        # 超乳
        source['b_pleasure_source'] *= 2.5
    elif flag == '5':
        # 魔乳
        source['b_pleasure_source'] *= 3.0


def _hip_size2src(flag: str, source: dict[str, int | float]):
    """臀围对source的修正"""
    if flag == '-2':
        # 纤臀
        source['a_pleasure_source'] *= 0.6
    elif flag == '-1':
        # 小臀
        source['a_pleasure_source'] *= 0.8
    elif flag == '1':
        # 巨臀
        source['a_pleasure_source'] *= 1.2
    elif flag == '2':
        # 丰满
        source['a_pleasure_source'] *= 1.5
    elif flag == '3':
        # 爆臀
        source['a_pleasure_source'] *= 2.0
    elif flag == '4':
        # 超臀
        source['a_pleasure_source'] *= 2.5
