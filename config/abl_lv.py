# abl等级上限
JUEL2ABL_MAX_LV: int = 13
EXP2ABL_MAX_LV: int = 6

# abl升级规则
ABL_LV: dict[int, int] = {
    # abl: exp
    0: 0,
    1: 1,
    2: 4,
    3: 20,
    4: 50,
    5: 200,
    6: 500,
    7: 1000,
    8: 2000,
    9: 3000,
    10: 4000,
    11: 5000,
    12: 6000,
    13: 10000
}

EXP_LV: dict[int, int] = {
    # exp: abl
    0: 0,
    1: 1,
    4: 2,
    20: 3,
    50: 4,
    200: 5,
    500: 6,
    1000: 7,
    2000: 8,
    3000: 9,
    4000: 10,
    5000: 11,
    6000: 12,
    10000: 13
}

EXP2ABL: set[str] = {
    'talk_exp', 'work_exp'
}