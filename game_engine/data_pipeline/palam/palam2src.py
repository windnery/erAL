# 修正系数
K_ACCEL = 0.3

def palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''palam_lv对source的修正'''
    if palam_lv['c_pleasure_palam'] > 0:
        source = _pleasure_palam2src('c_pleasure_palam', palam_lv, source)
    if palam_lv['v_pleasure_palam'] > 0:
        source = _pleasure_palam2src('v_pleasure_palam', palam_lv, source)
    if palam_lv['a_pleasure_palam'] > 0:
        source = _pleasure_palam2src('a_pleasure_palam', palam_lv, source)
    if palam_lv['b_pleasure_palam'] > 0:
        source = _pleasure_palam2src('b_pleasure_palam', palam_lv, source)
    if palam_lv['m_pleasure_palam'] > 0:
        source = _pleasure_palam2src('m_pleasure_palam', palam_lv, source)
    if palam_lv['lubrication_palam'] > 0:
        source = _lubrication_palam2src(palam_lv, source)
    if palam_lv['obedience_palam'] > 0:
        source = _obedience_palam2src(palam_lv, source)
    if palam_lv['lust_palam'] > 0:
        source = _lust_palam2src(palam_lv, source)
    if palam_lv['submission_palam'] > 0:
        source = _submission_palam2src(palam_lv, source)
    if palam_lv['learn_palam'] > 0:
        source = _learn_palam2src(palam_lv, source)
    if palam_lv['shame_palam'] > 0:
        source = _shame_palam2src(palam_lv, source)
    if palam_lv['pain_palam'] > 0:
        source = _pain_palam2src(palam_lv, source)
    if palam_lv['fear_palam'] > 0:
        source = _fear_palam2src(palam_lv, source)
    if palam_lv['kindness_palam'] > 0:
        source = _kindness_palam2src(palam_lv, source)
    if palam_lv['superiority_palam'] > 0:
        source = _superiority_palam2src(palam_lv, source)
    if palam_lv['disgust_palam'] > 0:
        source = _disgust_palam2src(palam_lv, source)
    if palam_lv['unhappiness_palam'] > 0:
        source = _unhappiness_palam2src(palam_lv, source)
    if palam_lv['depression_palam'] > 0:
        source = _depression_palam2src(palam_lv, source)

    return source


def _pleasure_palam2src(palam: str, palam_lv: dict[str, int], source: dict[str, int]):
    '''pleasure_palam等级对source的修正'''
    pleasure_lv = palam_lv[palam]
    pleasure_source = palam.replace('palam', 'source')
    modify = pleasure_lv * (1 + K_ACCEL * (pleasure_lv - 1) / 2)
    source[pleasure_source] += int(4 * modify) if source[pleasure_source] else 0
    source['lubrication_source'] += int(3 * modify) if source['lubrication_source'] else 0
    source['love_source'] += int(2 * modify) if source['love_source'] else 0
    source['sex_act_source'] += int(2 * modify) if source['sex_act_source'] else 0
    source['lust_source'] += int(2 * modify) if source['lust_source'] else 0
    source['obedience_source'] += int(2 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(2 * modify) if source['submission_source'] else 0
    source['happiness_source'] += int(3 * modify) if source['happiness_source'] else 0
    source['conquest_source'] += int(2 * modify) if source['conquest_source'] else 0
    source['exposure_source'] += int(2 * modify) if source['exposure_source'] else 0
    source['passivity_source'] += int(2 * modify) if source['passivity_source'] else 0
    source['achievement_source'] += int(2 * modify) if source['achievement_source'] else 0
    # 负向修正
    source['pain_source'] -= min(source['pain_source'], int(1 * modify)) if source['pain_source'] else 0
    source['fear_source'] -= min(source['fear_source'], int(1 * modify)) if source['fear_source'] else 0
    source['disgust_source'] -= min(source['disgust_source'], int(1 * modify)) if source['disgust_source'] else 0
    source['unclean_source'] -= min(source['unclean_source'], int(1 * modify)) if source['unclean_source'] else 0
    source['depression_source'] -= min(source['depression_source'], int(1 * modify)) if source['depression_source'] else 0
    source['escape_source'] -= min(source['escape_source'], int(1 * modify)) if source['escape_source'] else 0

    return source

def _lubrication_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''lubrication_palam等级对source的修正'''
    lubrication_lv = palam_lv['lubrication_palam']
    modify = lubrication_lv * (1 + K_ACCEL * (lubrication_lv - 1) / 2)
    source['c_pleasure_source'] += int(3 * modify) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] += int(3 * modify) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] += int(3 * modify) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] += int(3 * modify) if source['b_pleasure_source'] else 0

    return source

def _obedience_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''obedience_palam等级对source的修正'''
    obedience_lv = palam_lv['obedience_palam']
    modify = obedience_lv * (1 + K_ACCEL * (obedience_lv - 1) / 2)
    source['love_source'] += int(3 * modify) if source['love_source'] else 0
    source['obedience_source'] += int(4 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(2 * modify) if source['submission_source'] else 0
    source['conquest_source'] += int(3 * modify) if source['conquest_source'] else 0
    # 负向修正
    source['fear_source'] -= min(source['fear_source'], int(1 * modify)) if source['fear_source'] else 0
    source['escape_source'] -= min(source['escape_source'], int(1 * modify)) if source['escape_source'] else 0
    source['disgust_source'] -= min(source['disgust_source'], int(1 * modify)) if source['disgust_source'] else 0

    return source

def _lust_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''lust_palam等级对source的修正'''
    lust_lv = palam_lv['lust_palam']
    modify = lust_lv * (1 + K_ACCEL * (lust_lv - 1) / 2)
    source['c_pleasure_source'] += int(2 * modify) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] += int(2 * modify) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] += int(2 * modify) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] += int(2 * modify) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] += int(2 * modify) if source['m_pleasure_source'] else 0
    source['love_source'] += int(2 * modify) if source['love_source'] else 0
    source['sex_act_source'] += int(2 * modify) if source['sex_act_source'] else 0
    source['lust_source'] += int(4 * modify) if source['lust_source'] else 0
    source['obedience_source'] += int(2 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(2 * modify) if source['submission_source'] else 0
    source['happiness_source'] += int(2 * modify) if source['happiness_source'] else 0
    source['conquest_source'] += int(1 * modify) if source['conquest_source'] else 0
    source['exposure_source'] += int(1 * modify) if source['exposure_source'] else 0
    source['passivity_source'] += int(1 * modify) if source['passivity_source'] else 0
    source['achievement_source'] += int(1 * modify) if source['achievement_source'] else 0
    source['lubrication_source'] += int(2 * modify) if source['lubrication_source'] else 0
    # 负向修正
    source['pain_source'] -= min(source['pain_source'], int(1 * modify)) if source['pain_source'] else 0
    source['fear_source'] -= min(source['fear_source'], int(1 * modify)) if source['fear_source'] else 0
    source['escape_source'] -= min(source['escape_source'], int(1 * modify)) if source['escape_source'] else 0
    source['disgust_source'] -= min(source['disgust_source'], int(1 * modify)) if source['disgust_source'] else 0
    source['unclean_source'] -= min(source['unclean_source'], int(1 * modify)) if source['unclean_source'] else 0
    source['depression_source'] -= min(source['depression_source'], int(1 * modify)) if source['depression_source'] else 0
    
    return source

def _submission_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''submission_palam等级对source的修正'''
    submission_lv = palam_lv['submission_palam']
    modify = submission_lv * (1 + K_ACCEL * (submission_lv - 1) / 2)
    source['sex_act_source'] += int(2 * modify) if source['sex_act_source'] else 0
    source['lust_source'] += int(2 * modify) if source['lust_source'] else 0
    source['obedience_source'] += int(3 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(4 * modify) if source['submission_source'] else 0
    source['conquest_source'] += int(3 * modify) if source['conquest_source'] else 0
    source['passivity_source'] += int(3 * modify) if source['passivity_source'] else 0
    source['achievement_source'] += int(3 * modify) if source['achievement_source'] else 0
    # 负向修正
    source['fear_source'] -= min(source['fear_source'], int(1 * modify)) if source['fear_source'] else 0
    source['escape_source'] -= min(source['escape_source'], int(2 * modify)) if source['escape_source'] else 0
    source['disgust_source'] -= min(source['disgust_source'], int(1 * modify)) if source['disgust_source'] else 0
    source['unclean_source'] -= min(source['unclean_source'], int(1 * modify)) if source['unclean_source'] else 0
    source['depression_source'] -= min(source['depression_source'], int(1 * modify)) if source['depression_source'] else 0

    return source

def _learn_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''learn_palam等级对source的修正'''
    learn_lv = palam_lv['learn_palam']
    modify = learn_lv * (1 + K_ACCEL * (learn_lv - 1) / 2)
    source['sex_act_source'] += int(2 * modify) if source['sex_act_source'] else 0
    source['obedience_source'] += int(2 * modify) if source['obedience_source'] else 0
    source['conquest_source'] += int(2 * modify) if source['conquest_source'] else 0
    source['achievement_source'] += int(3 * modify) if source['achievement_source'] else 0
        
    return source

def _shame_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''shame_palam等级对source的修正'''
    shame_lv = palam_lv['shame_palam']
    modify = shame_lv * (1 + K_ACCEL * (shame_lv - 1) / 2)
    source['c_pleasure_source'] += int(1 * modify) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] += int(1 * modify) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] += int(1 * modify) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] += int(1 * modify) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] += int(1 * modify) if source['m_pleasure_source'] else 0
    source['lust_source'] += int(2 * modify) if source['lust_source'] else 0
    source['obedience_source'] += int(2 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(2 * modify) if source['submission_source'] else 0
    source['happiness_source'] += int(1 * modify) if source['happiness_source'] else 0
    source['conquest_source'] += int(1 * modify) if source['conquest_source'] else 0
    source['passivity_source'] += int(3 * modify) if source['passivity_source'] else 0
    source['achievement_source'] += int(1 * modify) if source['achievement_source'] else 0
    source['escape_source'] += int(1 * modify) if source['escape_source'] else 0
    source['disgust_source'] += int(1 * modify) if source['disgust_source'] else 0
    # 负向修正
    source['exposure_source'] -= min(source['exposure_source'], int(1 * modify)) if source['exposure_source'] else 0

    return source

def _pain_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''pain_palam等级对source的修正'''
    pain_lv = palam_lv['pain_palam']
    modify = pain_lv * (1 + K_ACCEL * (pain_lv - 1) / 2)
    source['pain_source'] += int(3 * modify) if source['pain_source'] else 0
    source['fear_source'] += int(3 * modify) if source['fear_source'] else 0
    source['submission_source'] += int(3 * modify) if source['submission_source'] else 0
    source['conquest_source'] += int(3 * modify) if source['conquest_source'] else 0
    source['passivity_source'] += int(3 * modify) if source['passivity_source'] else 0
    source['depression_source'] += int(3 * modify) if source['depression_source'] else 0
    source['escape_source'] += int(4 * modify) if source['escape_source'] else 0
    source['disgust_source'] += int(3 * modify) if source['disgust_source'] else 0
    # 负向修正
    source['c_pleasure_source'] -= min(source['c_pleasure_source'], int(3 * modify)) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] -= min(source['v_pleasure_source'], int(3 * modify)) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] -= min(source['a_pleasure_source'], int(3 * modify)) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] -= min(source['b_pleasure_source'], int(3 * modify)) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] -= min(source['m_pleasure_source'], int(3 * modify)) if source['m_pleasure_source'] else 0
    source['lust_source'] -= min(source['lust_source'], int(2 * modify)) if source['lust_source'] else 0
    source['obedience_source'] -= min(source['obedience_source'], int(3 * modify)) if source['obedience_source'] else 0
    source['exposure_source'] -= min(source['exposure_source'], int(1 * modify)) if source['exposure_source'] else 0
    source['lubrication_source'] -= min(source['lubrication_source'], int(1 * modify)) if source['lubrication_source'] else 0
    source['love_source'] -= min(source['love_source'], int(3 * modify)) if source['love_source'] else 0
    source['achievement_source'] -= min(source['achievement_source'], int(2 * modify)) if source['achievement_source'] else 0
    source['happiness_source'] -= min(source['happiness_source'], int(3 * modify)) if source['happiness_source'] else 0

    return source

def _fear_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''fear_palam等级对source的修正'''
    fear_lv = palam_lv['fear_palam']
    modify = fear_lv * (1 + K_ACCEL * (fear_lv - 1) / 2)
    source['pain_source'] += int(3 * modify) if source['pain_source'] else 0
    source['fear_source'] += int(4 * modify) if source['fear_source'] else 0
    source['obedience_source'] += int(2 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(3 * modify) if source['submission_source'] else 0
    source['conquest_source'] += int(4 * modify) if source['conquest_source'] else 0
    source['passivity_source'] += int(3 * modify) if source['passivity_source'] else 0
    source['depression_source'] += int(3 * modify) if source['depression_source'] else 0
    source['escape_source'] += int(4 * modify) if source['escape_source'] else 0
    source['disgust_source'] += int(3 * modify) if source['disgust_source'] else 0
    # 负向修正
    source['c_pleasure_source'] -= min(source['c_pleasure_source'], int(2 * modify)) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] -= min(source['v_pleasure_source'], int(2 * modify)) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] -= min(source['a_pleasure_source'], int(2 * modify)) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] -= min(source['b_pleasure_source'], int(2 * modify)) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] -= min(source['m_pleasure_source'], int(2 * modify)) if source['m_pleasure_source'] else 0
    source['lubrication_source'] -= min(source['lubrication_source'], int(1 * modify)) if source['lubrication_source'] else 0
    source['love_source'] -= min(source['love_source'], int(3 * modify)) if source['love_source'] else 0
    source['achievement_source'] -= min(source['achievement_source'], int(2 * modify)) if source['achievement_source'] else 0
    source['lust_source'] -= min(source['lust_source'], int(2 * modify)) if source['lust_source'] else 0
    source['exposure_source'] -= min(source['exposure_source'], int(1 * modify)) if source['exposure_source'] else 0
    source['happiness_source'] -= min(source['happiness_source'], int(3 * modify)) if source['happiness_source'] else 0

    return source

def _kindness_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''kindness_palam等级对source的修正'''
    kindness_lv = palam_lv['kindness_palam']
    modify = kindness_lv * (1 + K_ACCEL * (kindness_lv - 1) / 2)
    source['c_pleasure_source'] += int(2 * modify) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] += int(2 * modify) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] += int(2 * modify) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] += int(2 * modify) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] += int(2 * modify) if source['m_pleasure_source'] else 0
    source['love_source'] += int(3 * modify) if source['love_source'] else 0
    source['achievement_source'] += int(2 * modify) if source['achievement_source'] else 0
    source['lust_source'] += int(2 * modify) if source['lust_source'] else 0
    source['obedience_source'] += int(2 * modify) if source['obedience_source'] else 0
    source['submission_source'] += int(2 * modify) if source['submission_source'] else 0
    source['happiness_source'] += int(3 * modify) if source['happiness_source'] else 0
    source['conquest_source'] += int(1 * modify) if source['conquest_source'] else 0
    source['passivity_source'] += int(1 * modify) if source['passivity_source'] else 0
    # 负向修正
    source['pain_source'] -= min(source['pain_source'], int(2 * modify)) if source['pain_source'] else 0
    source['fear_source'] -= min(source['fear_source'], int(2 * modify)) if source['fear_source'] else 0
    source['unclean_source'] -= min(source['unclean_source'], int(1 * modify)) if source['unclean_source'] else 0
    source['disgust_source'] -= min(source['disgust_source'], int(2 * modify)) if source['disgust_source'] else 0
    source['escape_source'] -= min(source['escape_source'], int(1 * modify)) if source['escape_source'] else 0
    source['depression_source'] -= min(source['depression_source'], int(2 * modify)) if source['depression_source'] else 0

    return source

def _superiority_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''superiority_palam等级对source的修正'''
    superiority_lv = palam_lv['superiority_palam']
    modify = superiority_lv * (1 + K_ACCEL * (superiority_lv - 1) / 2)
    source['happiness_source'] += int(1 * modify) if source['happiness_source'] else 0
    source['depression_source'] += int(1 * modify) if source['depression_source'] else 0
    # 负向修正
    source['fear_source'] -= min(source['fear_source'], int(1 * modify)) if source['fear_source'] else 0
    source['obedience_source'] -= min(source['obedience_source'], int(1 * modify)) if source['obedience_source'] else 0
    source['submission_source'] -= min(source['submission_source'], int(1 * modify)) if source['submission_source'] else 0
    source['conquest_source'] -= min(source['conquest_source'], int(2 * modify)) if source['conquest_source'] else 0
    source['passivity_source'] -= min(source['passivity_source'], int(2 * modify)) if source['passivity_source'] else 0
    source['escape_source'] -= min(source['escape_source'], int(1 * modify)) if source['escape_source'] else 0

    return source

def _disgust_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''disgust_palam等级对source的修正'''
    disgust_lv = palam_lv['disgust_palam']
    modify = disgust_lv * (1 + K_ACCEL * (disgust_lv - 1) / 2)
    source['fear_source'] += int(1 * modify) if source['fear_source'] else 0
    source['depression_source'] += int(3 * modify) if source['depression_source'] else 0
    source['escape_source'] += int(3 * modify) if source['escape_source'] else 0
    source['disgust_source'] += int(4 * modify) if source['disgust_source'] else 0
    # 负向修正
    source['c_pleasure_source'] -= min(source['c_pleasure_source'], int(1 * modify)) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] -= min(source['v_pleasure_source'], int(1 * modify)) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] -= min(source['a_pleasure_source'], int(1 * modify)) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] -= min(source['b_pleasure_source'], int(1 * modify)) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] -= min(source['m_pleasure_source'], int(1 * modify)) if source['m_pleasure_source'] else 0
    source['lubrication_source'] -= min(source['lubrication_source'], int(1 * modify)) if source['lubrication_source'] else 0
    source['love_source'] -= min(source['love_source'], int(3 * modify)) if source['love_source'] else 0
    source['achievement_source'] -= min(source['achievement_source'], int(2 * modify)) if source['achievement_source'] else 0
    source['lust_source'] -= min(source['lust_source'], int(2 * modify)) if source['lust_source'] else 0
    source['obedience_source'] -= min(source['obedience_source'], int(3 * modify)) if source['obedience_source'] else 0
    source['exposure_source'] -= min(source['exposure_source'], int(1 * modify)) if source['exposure_source'] else 0
    source['submission_source'] -= min(source['submission_source'], int(2 * modify)) if source['submission_source'] else 0
    source['happiness_source'] -= min(source['happiness_source'], int(3 * modify)) if source['happiness_source'] else 0
    source['conquest_source'] -= min(source['conquest_source'], int(2 * modify)) if source['conquest_source'] else 0

    return source

def _unhappiness_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''unhappiness_palam等级对source的修正'''
    unhappiness_lv = palam_lv['unhappiness_palam']
    modify = unhappiness_lv * (1 + K_ACCEL * (unhappiness_lv - 1) / 2)
    source['fear_source'] += int(1 * modify) if source['fear_source'] else 0
    source['depression_source'] += int(3 * modify) if source['depression_source'] else 0
    source['escape_source'] += int(3 * modify) if source['escape_source'] else 0
    source['disgust_source'] += int(4 * modify) if source['disgust_source'] else 0
    # 负向修正
    source['c_pleasure_source'] -= min(source['c_pleasure_source'], int(3 * modify)) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] -= min(source['v_pleasure_source'], int(3 * modify)) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] -= min(source['a_pleasure_source'], int(3 * modify)) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] -= min(source['b_pleasure_source'], int(3 * modify)) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] -= min(source['m_pleasure_source'], int(3 * modify)) if source['m_pleasure_source'] else 0
    source['lubrication_source'] -= min(source['lubrication_source'], int(1 * modify)) if source['lubrication_source'] else 0
    source['love_source'] -= min(source['love_source'], int(3 * modify)) if source['love_source'] else 0
    source['achievement_source'] -= min(source['achievement_source'], int(2 * modify)) if source['achievement_source'] else 0
    source['lust_source'] -= min(source['lust_source'], int(2 * modify)) if source['lust_source'] else 0
    source['obedience_source'] -= min(source['obedience_source'], int(3 * modify)) if source['obedience_source'] else 0
    source['exposure_source'] -= min(source['exposure_source'], int(1 * modify)) if source['exposure_source'] else 0
    source['submission_source'] -= min(source['submission_source'], int(2 * modify)) if source['submission_source'] else 0
    source['happiness_source'] -= min(source['happiness_source'], int(3 * modify)) if source['happiness_source'] else 0
    source['conquest_source'] -= min(source['conquest_source'], int(2 * modify)) if source['conquest_source'] else 0

    return source

def _depression_palam2src(palam_lv: dict[str, int], source: dict[str, int]):
    '''depression_palam等级对source的修正'''
    depression_lv = palam_lv['depression_palam']
    modify = depression_lv * (1 + K_ACCEL * (depression_lv - 1) / 2)
    source['fear_source'] += int(2 * modify) if source['fear_source'] else 0
    source['passivity_source'] += int(1 * modify) if source['passivity_source'] else 0
    source['depression_source'] += int(4 * modify) if source['depression_source'] else 0
    source['escape_source'] += int(2 * modify) if source['escape_source'] else 0
    source['disgust_source'] += int(3 * modify) if source['disgust_source'] else 0
    # 负向修正
    source['c_pleasure_source'] -= min(source['c_pleasure_source'], int(3 * modify)) if source['c_pleasure_source'] else 0
    source['v_pleasure_source'] -= min(source['v_pleasure_source'], int(3 * modify)) if source['v_pleasure_source'] else 0
    source['a_pleasure_source'] -= min(source['a_pleasure_source'], int(3 * modify)) if source['a_pleasure_source'] else 0
    source['b_pleasure_source'] -= min(source['b_pleasure_source'], int(3 * modify)) if source['b_pleasure_source'] else 0
    source['m_pleasure_source'] -= min(source['m_pleasure_source'], int(3 * modify)) if source['m_pleasure_source'] else 0
    source['lubrication_source'] -= min(source['lubrication_source'], int(1 * modify)) if source['lubrication_source'] else 0
    source['love_source'] -= min(source['love_source'], int(3 * modify)) if source['love_source'] else 0
    source['sex_act_source'] -= min(source['sex_act_source'], int(1 * modify)) if source['sex_act_source'] else 0
    source['achievement_source'] -= min(source['achievement_source'], int(2 * modify)) if source['achievement_source'] else 0
    source['lust_source'] -= min(source['lust_source'], int(2 * modify)) if source['lust_source'] else 0
    source['obedience_source'] -= min(source['obedience_source'], int(2 * modify)) if source['obedience_source'] else 0
    source['exposure_source'] -= min(source['exposure_source'], int(1 * modify)) if source['exposure_source'] else 0
    source['submission_source'] -= min(source['submission_source'], int(2 * modify)) if source['submission_source'] else 0
    source['happiness_source'] -= min(source['happiness_source'], int(3 * modify)) if source['happiness_source'] else 0
    source['conquest_source'] -= min(source['conquest_source'], int(2 * modify)) if source['conquest_source'] else 0

    return source
