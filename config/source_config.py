ALL_SOURCE_KEYS: set[str] = {
    'c_pleasure_source', 'v_pleasure_source', 'a_pleasure_source',
    'b_pleasure_source', 'm_pleasure_source', 'lubrication_source',
    'love_source', 'sex_act_source', 'lust_source', 'obedience_source',
    'submission_source', 'happiness_source', 'conquest_source',
    'exposure_source', 'passivity_source', 'achievement_source',
    'pain_source', 'fear_source', 'disgust_source', 'unclean_source',
    'depression_source', 'escape_source',
}
POSITIVE_SRC: set[str] = {
    'c_pleasure_source', 'v_pleasure_source',
    'a_pleasure_source', 'b_pleasure_source',
    'm_pleasure_source', 'love_source',
    'lust_source', 'happiness_source',
    'conquest_source', 'passivity_source',
    'obedience_source', 'submission_source',
    'exposure_source', 'achievement_source',
    'lubrication_source', 'sex_act_source'
}
NEGATIVE_SRC: set[str] = {
    'pain_source', 'fear_source',
    'unclean_source', 'depression_source',
    'escape_source', 'disgust_source'
}

# =================================================
"""理性相关"""
# 理性逆向
RATIONALITY_NEG_SRC_WEIGHT: int = 12
RATIONALITY_NEG_SRC: set[str] = {
    'c_pleasure_source', 'v_pleasure_source', 'a_pleasure_source',
    'b_pleasure_source', 'm_pleasure_source', 'love_source',
    'lust_source', 'happiness_source', 'conquest_source',
    'obedience_source', 'submission_source', 'achievement_source'
}
# 理性正向
RATIONALITY_POS_SRC_WEIGHT: int = 8
RATIONALITY_POS_SRC: set[str] = {
    'fear_source', 'disgust_source', 'pain_source'
}

"""情绪相关"""
# 情绪正向1
EMOTION_POS_SRC1_WEIGHT: int = 15
EMOTION_POS_SRC1: set[str] = {
    'c_pleasure_source', 'v_pleasure_source', 'a_pleasure_source',
    'b_pleasure_source', 'm_pleasure_source', 'love_source',
    'lust_source'
}
# 情绪正向2
EMOTION_POS_SRC2_WEIGHT: int = 10
EMOTION_POS_SRC2: set[str] = {
    'happiness_source', 'conquest_source', 'obedience_source',
    'submission_source', 'achievement_source'
}
# 情绪逆向1
EMOTION_NEG_SRC1_WEIGHT: int = 12
EMOTION_NEG_SRC1: set[str] = {
    'pain_source', 'fear_source',
    'depression_source', 'disgust_source'
}
# 情绪逆向2
EMOTION_NEG_SRC2_WEIGHT: int = 8
EMOTION_NEG_SRC2: set[str] = {
    'escape_source', 'unclean_source'
}
# =================================================
