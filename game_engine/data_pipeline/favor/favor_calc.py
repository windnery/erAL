from game_engine.data_pipeline.palam.palam2favor import palam2favor
from game_engine.data_pipeline.mood.mood2favor import mood2favor
from game_engine.models.shipgirl import ShipGirl


def favor_calc(npc: ShipGirl, source: dict[str, int]) -> int:
    '''好感度上升计算处理'''
    favor_delta = 0

    # abl: 顺从 亲密
    favor_delta += (npc.abl['obedience_abl'] + npc.abl['intimacy_abl']) // 2

    # TODO: 素质

    temp = 0
    # 各种快感
    # TODO: 这里缺个快感应答
    temp += (100 - 30_000 / (source.get('c_pleasure_source', 0) +\
                            source.get('v_pleasure_source', 0) +\
                            source.get('a_pleasure_source', 0) +\
                            source.get('b_pleasure_source', 0) + 300))
    # 情爱
    temp += (100 - 100_000 / (source.get('love_source', 0) + 1000))
    # 欲情
    temp += (20 - 20_000 / (source.get('lust_source', 0) + 1000))
    # 达成
    temp += (30 - 30_000 / (source.get('achievement_source', 0) + 1000))
    # 恭顺
    temp += (20 - 20_000 / (source.get('obedience_source', 0) + 1000))
    # 屈服
    temp += (20 - 20_000 / (source.get('submission_source', 0) + 1000))
    # 露出
    temp += (30 - 30_000 / (source.get('exposure_source', 0) + 1000)) * (npc.abl['exposure_abl'] - 3) // 3
    # 苦痛
    temp += (50 - 20_000 / (source.get('pain_source', 0) + 400)) * (npc.abl['masochistic_abl'] - 3) // 3
    # 欢乐
    temp += (50 - 10_000 / (source.get('happiness_source', 0) + 2000))
    # 征服
    temp += (30 - 90_000 / (source.get('conquest_source', 0) + 3000))
    # 被动
    temp += (30 - 90_000 / (source.get('passivity_source', 0) + 3000))

    # 恐怖
    temp -= (50 - 20_000 / (source.get('fear_source', 0) + 400)) * (npc.abl['obedience_abl'] - 3) // 3
    # 不洁 TODO: 这里缺个污臭耐性
    temp -= (50 - 25_000 / (source.get('unclean_source', 0) + 500))
    # 抑郁
    temp -= (50 - 15_000 / (source.get('depression_source', 0) + 300))
    # 逃逸
    temp -= (50 - 25_000 / (source.get('escape_source', 0) + 500))
    # 反感
    temp -= (50 - 10_000 / (source.get('disgust_source', 0) + 200))

    favor_delta += int(temp // 10)
    # 心情
    favor_delta += mood2favor(npc.get_mood())
    # palam等级对好感的修正
    favor_delta += palam2favor(npc.palam_lv)
    return favor_delta