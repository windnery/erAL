from config.source_config import EMOTION_POS_SRC1, EMOTION_POS_SRC1_WEIGHT, EMOTION_POS_SRC2_WEIGHT, EMOTION_POS_SRC2, \
    EMOTION_NEG_SRC1, EMOTION_NEG_SRC1_WEIGHT, EMOTION_NEG_SRC2, EMOTION_NEG_SRC2_WEIGHT, RATIONALITY_POS_SRC, \
    RATIONALITY_POS_SRC_WEIGHT, RATIONALITY_NEG_SRC, RATIONALITY_NEG_SRC_WEIGHT
from game_engine.models.shipgirl import ShipGirl


def emotion_rationality_calc(source: dict[str, int], npc: ShipGirl):
    """情绪&理性计算"""
    e_score, r_score = 0, 0
    for src, value in source.items():
        if src in EMOTION_POS_SRC1:
            # 情绪正向1
            e_score += value * EMOTION_POS_SRC1_WEIGHT
        elif src in EMOTION_POS_SRC2:
            # 情绪正向2
            e_score += value * EMOTION_POS_SRC2_WEIGHT
        elif src in EMOTION_NEG_SRC1:
            # 情绪负向1
            e_score -= value * EMOTION_NEG_SRC1_WEIGHT
        elif src in EMOTION_NEG_SRC2:
            # 情绪负向2
            e_score -= value * EMOTION_NEG_SRC2_WEIGHT

        if src in RATIONALITY_POS_SRC:
            # 理性正向
            r_score += value * RATIONALITY_POS_SRC_WEIGHT
        elif src in RATIONALITY_NEG_SRC:
            # 理性负向
            r_score -= value * RATIONALITY_NEG_SRC_WEIGHT

    e_score //= 1000
    r_score //= 1000
    npc.set_emotion(npc.get_emotion() + e_score)
    npc.set_rationality(npc.get_rationality() + r_score)