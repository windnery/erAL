def palam2trust(palam_lv: dict[str, int]):
    """palam等级对信赖的修正"""
    bonus = 0

    # 好意 恭顺
    kindness_lv = palam_lv['kindness_palam']
    obedience_lv = palam_lv['obedience_palam']
    if kindness_lv + obedience_lv < 3:
        pass
    elif kindness_lv + obedience_lv < 6:
        bonus += 1
    elif kindness_lv + obedience_lv < 9:
        bonus += 2
    elif kindness_lv + obedience_lv < 12:
        bonus += 3
    else:
        bonus += 4

    # 反感 不快 抑郁 苦痛 恐怖
    disgust_lv = palam_lv['disgust_palam']
    unhappiness_lv = palam_lv['unhappiness_palam']
    depression_lv = palam_lv['depression_palam']
    pain_lv = palam_lv['pain_palam']
    fear_lv = palam_lv['fear_palam']
    if disgust_lv + unhappiness_lv + depression_lv + pain_lv + fear_lv < 3:
        pass
    elif disgust_lv + unhappiness_lv + depression_lv + pain_lv + fear_lv < 6:
        bonus -= 1
    elif disgust_lv + unhappiness_lv + depression_lv + pain_lv + fear_lv < 9:
        bonus -= 2
    elif disgust_lv + unhappiness_lv + depression_lv + pain_lv + fear_lv < 12:
        bonus -= 3
    else:
        bonus -= 4

    return bonus