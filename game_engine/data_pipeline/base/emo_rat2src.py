from config.source_config import POSITIVE_SRC, NEGATIVE_SRC
from game_engine.models.shipgirl import ShipGirl


def emo_rat2src(npc: ShipGirl, source: dict[str, int | float]):
    """情绪&理性对source的修正"""
    emotion = npc.get_emotion()
    rationality = npc.get_rationality()
    emo_p_weight = emo_n_weight = rat_p_weight = rat_n_weight = 1

    if 100 <= emotion < 250:
        emo_p_weight = 1.25
        emo_n_weight = 0.9
    elif 250 <= emotion < 500:
        emo_p_weight = 1.5
        emo_n_weight = 0.75
    elif 500 <= emotion < 750:
        emo_p_weight = 1.75
        emo_n_weight = 0.6
    elif 750 <= emotion <= 1000:
        emo_p_weight = 2
        emo_n_weight = 0.5

    if 0 <= rationality < 250:
        rat_p_weight = 2
        rat_n_weight = 0.5
    elif 250 <= rationality < 500:
        rat_p_weight = 1.75
        rat_n_weight = 0.6
    elif 500 <= rationality < 750:
        rat_p_weight = 1.5
        rat_n_weight = 0.75
    elif 750 <= rationality <= 900:
        rat_p_weight = 1.25
        rat_n_weight = 0.9

    for k, v in source.items():
        if k in POSITIVE_SRC:
            source[k] = int(v * emo_p_weight * rat_p_weight)
        elif k in NEGATIVE_SRC:
            source[k] = int(v * emo_n_weight * rat_n_weight)
