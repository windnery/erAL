from config.source_kind import POSITIVE_SRC, NEGATIVE_SRC

ABL_SRC_WEIGHTS = {
    'c_sen_abl': {
        'c_pleasure_source': 4,
        'lubrication_source': 2,
        'sex_act_source': 2,
        'lust_source': 1,
    },
    'v_sen_abl': {
        'v_pleasure_source': 4,
        'lubrication_source': 2,
        'sex_act_source': 2,
        'lust_source': 1,
    },
    'a_sen_abl': {
        'a_pleasure_source': 4,
        'lubrication_source': 2,
        'sex_act_source': 2,
        'lust_source': 1,
    },
    'b_sen_abl': {
        'b_pleasure_source': 4,
        'lubrication_source': 2,
        'sex_act_source': 2,
        'lust_source': 1,
    },
    'm_sen_abl': {
        's_pleasure_source': 4,
        'lubrication_source': 2,
        'sex_act_source': 2,
        'lust_source': 1,
    },
    'intimacy_abl': {src: 2 for src in POSITIVE_SRC} | {src: -1 for src in NEGATIVE_SRC},
    'obedience_abl': {src: 1 for src in POSITIVE_SRC} | {src: -1 for src in NEGATIVE_SRC},
    'desire_abl': {
        'lubrication_source': 2,
        'sex_act_source': 2,
        'lust_source': 4,
        'exposure_source': 2,
        'fear_source': -2,
        'unclean_source': -1,
        'depression_source': -1,
        'escape_source': -2,
        'disgust_source': -2,
    },
    'skill_abl': {
        'achievement_source': 4,
        'conquest_source': 2
    },
    'servant_abl': {
        'love_source': 3,
        'obedience_source': 3,
        'submission_source': 2,
        'happiness_source': 2,
        'exposure_source': 2,
        'passivity_source': 3,
        'achievement_source': 2,
        'pain_source': -1,
        'fear_source': -1,
        'disgust_source': -2,
        'unclean_source': -1,
        'depression_source': -1,
        'escape_source': -2,
    },
    'exposure_abl': {
        'exposure_source': 4,
        'lust_source': 2,
        'sex_act_source': 2,
        'escape_source': -2,
    },
    'masochistic_abl': {
        'sex_act_source': 2,
        'lust_source': 2,
        'obedience_source': 2,
        'submission_source': 2,
        'passivity_source': 3,
        'conquest_source': -2,
        'fear_source': -2,
        'escape_source': -2,
    },
    'sadism_abl': {
        'sex_act_source': 2,
        'lust_source': 2,
        'obedience_source': -2,
        'submission_source': -2,
        'passivity_source': -3,
        'conquest_source': 3,
    },
    'masturbation_addiction_abl': {
        'c_pleasure_source': 4,
        'v_pleasure_source': 4,
        'a_pleasure_source': 4,
        'b_pleasure_source': 4,
        'lust_source': 2,
        'sex_act_source': 3,
        'fear_source': -1,
        'unclean_source': -2,
        'escape_source': -2,
    },
    'semen_addiction_abl': {
        'sex_act_source': 5,
        'lust_source': 5,
        'unclean_source': -3
    },
    'v_semen_addiction_abl': {
        'v_pleasure_source': 5,
        'sex_act_source': 5,
        'lust_source': 5,
        'unclean_source': -3
    },
    'a_semen_addiction_abl': {
        'a_pleasure_source': 5,
        'sex_act_source': 5,
        'lust_source': 5,
        'unclean_source': -3
    }
}