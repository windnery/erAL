from game_engine.models.character import Character
from config.juel import JUEL_GET, JUEL_SET


def juel_calc(npc: Character):
    """珠子获得计算"""
    for palam_k, palam_v in npc.palam.items():
        juel_id = palam_k.replace('palam', 'juel')
        if juel_id not in JUEL_SET:
            continue

        best = 0
        for _palam_lv, juel in JUEL_GET.items():
            if palam_v >= _palam_lv:
                best = juel
            else: break
        if juel_id in ['depression_juel', 'disgust_juel', 'unhappiness_juel']:
            npc.juel['negation_juel'] += best
        else:
            npc.juel[juel_id] += best

    if npc.juel['negation_juel'] > 0:
        for juel_id in npc.juel.keys():
            if juel_id == 'negation_juel':
                continue
            num = min(npc.juel['negation_juel'], npc.juel[juel_id])
            npc.juel[juel_id] -= num
            npc.juel['negation_juel'] -= num

            if npc.juel['negation_juel'] == 0:
                break