from config.source_config import NEGATIVE_SRC, POSITIVE_SRC
from game_engine.models.shipgirl import ShipGirl


def emo_rat2src(npc: ShipGirl, source: dict[str, int | float]):
    """情绪&理性对source的修正"""
    emotion = npc.get_emotion()
    rationality = npc.get_rationality()
    emo_p_weight = emo_n_weight = rat_p_weight = rat_n_weight = 1

    if 100 <= emotion < 250:
        emo_p_weight = 1.1
        emo_n_weight = 0.9
    elif 250 <= emotion < 500:
        emo_p_weight = 1.2
        emo_n_weight = 0.8
    elif 500 <= emotion < 750:
        emo_p_weight = 1.3
        emo_n_weight = 0.7
    elif 750 <= emotion <= 1000:
        emo_p_weight = 1.5
        emo_n_weight = 0.6

    if 0 <= rationality < 250:
        # rat_p_weight = 1.5
        rat_n_weight = 0.6
    elif 250 <= rationality < 500:
        # rat_p_weight = 1.3
        rat_n_weight = 0.7
    elif 500 <= rationality < 750:
        # rat_p_weight = 1.3
        rat_n_weight = 0.8
    elif 750 <= rationality <= 900:
        # rat_p_weight = 1.2
        rat_n_weight = 0.9

    for k, v in source.items():
        if k in POSITIVE_SRC:
            source[k] = int(v * emo_p_weight)
        elif k in NEGATIVE_SRC:
            source[k] = int(v * emo_n_weight * rat_n_weight)
