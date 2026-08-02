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

NEGATIVE_SRC:set[str] = {
    'pain_source', 'fear_source',
    'unclean_source', 'depression_source',
    'escape_source', 'disgust_source'
}
