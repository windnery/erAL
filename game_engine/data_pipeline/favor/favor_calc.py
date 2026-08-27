from game_engine.data_pipeline.base.emo_rat2favor import emo_rat2favor
from game_engine.data_pipeline.palam.palam2favor import palam2favor
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl


def favor_calc(player: Player, npc: ShipGirl, source: dict[str, int]) -> int:
    """好感度上升计算处理"""
    favor_delta = 0

    # abl: 顺从 亲密
    favor_delta += (npc.abl['obedience_abl'] + npc.abl['intimacy_abl']) // 2

    # 叛逆
    if npc.get_talent_value('attitude') > 0:
        favor_delta -= 1
    # 坦率
    elif npc.get_talent_value('attitude') < 0:
        favor_delta += 1
    # 自尊心高
    if npc.get_talent_value('self_respect') > 0:
        favor_delta -= 1
    # 自制心
    if npc.has_talent('self_control'):
        favor_delta -= 1
    # 感情缺乏
    if npc.has_talent('emotional_deficiency'):
        favor_delta -= 1
    # 抵抗
    if npc.has_talent('resistance'):
        favor_delta -= 1
    # 献身的
    if npc.has_talent('devoted'):
        favor_delta += 1
    # 同时开朗
    if player.has_talent('bright') and npc.has_talent('bright'):
        favor_delta += 1
    # 同时阴郁
    if player.has_talent('morose') and npc.has_talent('morose'):
        favor_delta += 1
    # 玩家魅力
    favor_delta += player.get_talent_value('charm')
    # 陷落阶段
    favor_delta *= {1: 1.2, 2: 1.5, 3: 1.7, 4: 2.0}.get(npc.get_talent_value('relationship'), 1)
    # 恋人
    if player.has_talent('lover'):
        favor_delta *= 1.5
    favor_delta = int(favor_delta)

    temp = 0
    # 各种快感
    temp += (100 - 30_000 / (source.get('c_pleasure_source', 0) +
                             source.get('v_pleasure_source', 0) +
                             source.get('a_pleasure_source', 0) +
                             source.get('b_pleasure_source', 0) + 300)) * (
                    1 + npc.get_talent_value('pleasure_response'))
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
    temp += (50 - 40_000 / (source.get('happiness_source', 0) + 2000))
    # 征服
    temp += (30 - 90_000 / (source.get('conquest_source', 0) + 3000))
    # 被动
    temp += (30 - 90_000 / (source.get('passivity_source', 0) + 3000))

    if npc.base.get('emotion', 0) < 800:
        # 情绪>=800时无视负面source
        # 恐怖
        temp -= (50 - 20_000 / (source.get('fear_source', 0) + 400)) * (npc.abl['obedience_abl'] - 3) // 3
        # 不洁
        temp -= (50 - 25_000 / (source.get('unclean_source', 0) + 500)) * (2 - npc.get_talent_value('foul_tolerance')) // 2
        # 抑郁
        temp -= (50 - 15_000 / (source.get('depression_source', 0) + 300))
        # 逃逸
        temp -= (50 - 25_000 / (source.get('escape_source', 0) + 500))
        # 反感
        temp -= (50 - 10_000 / (source.get('disgust_source', 0) + 200))

    favor_delta += int(temp // 10)

    # palam等级对好感的修正
    favor_delta += palam2favor(npc.palam_lv)

    # 情绪&理性对好感的修正
    favor_delta += emo_rat2favor(npc.base.get('emotion', 0), npc.base.get('rationality', 1000))

    return favor_delta
