from game_engine.data_pipeline.base.emo_rat2trust import emo_rat2trust
from game_engine.data_pipeline.palam.palam2trust import palam2trust


def trust_calc(npc, source: dict[str, int]):
    """信赖上升计算处理"""
    trust_delta = 0

    # abl: 亲密
    trust_delta += (npc.abl['intimacy_abl'] // 5)

    # TODO: 素质

    temp = 0
    # 情爱
    temp += (50 - 250_000 / (source.get('love_source', 0) + 5000))
    # 达成
    temp += (30 - 30_000 / (source.get('achievement_source', 0) + 1000))
    # 恭顺
    temp += (20 - 20_000 / (source.get('obedience_source', 0) + 1000))
    # 屈服
    temp += (15 - 15_000 / (source.get('submission_source', 0) + 1000))
    # 欢乐
    temp += (30 - 150_000 / (source.get('happiness_source', 0) + 5000))
    # 征服
    temp += (30 - 90_000 / (source.get('conquest_source', 0) + 3000))
    # 被动
    temp += (30 - 90_000 / (source.get('passivity_source', 0) + 3000))

    low_rat = npc.base.get('rationality', 1000) < 200
    if npc.base.get('emotion', 0) < 800:
        # 情绪>=800时无视负面source
        # 理性<200时负面source影响减半"""
        # 苦痛
        temp -= (50 - 20_000 / (source.get('pain_source', 0) + 400)) * (npc.abl['masochistic_abl'] - 3) // 3 // (2 if low_rat else 1)
        # 恐怖
        temp -= (50 - 20_000 / (source.get('fear_source', 0) + 400)) * (npc.abl['obedience_abl'] - 3) // 3 // (2 if low_rat else 1)
        # 不洁 TODO: 这里缺个污臭耐性
        temp -= (50 - 25_000 / (source.get('unclean_source', 0) + 500)) // (2 if low_rat else 1)
        # 抑郁
        temp -= (50 - 15_000 / (source.get('depression_source', 0) + 300)) // (2 if low_rat else 1)
        # 逃逸
        temp -= (50 - 25_000 / (source.get('escape_source', 0) + 500)) // (2 if low_rat else 1)
        # 反感
        temp -= (50 - 10_000 / (source.get('disgust_source', 0) + 200)) // (2 if low_rat else 1)

    # palam等级对信赖的修正
    trust_delta += palam2trust(npc.palam)

    # 情绪&理性对信赖的修正
    trust_delta += emo_rat2trust(npc.base.get('emotion', 0), npc.base.get('rationality', 1000))

    trust_delta += int(temp // 10)

    return trust_delta