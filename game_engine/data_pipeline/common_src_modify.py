# 对source进行通用修正
from random import uniform

from config.source_kind import positive_src, negative_src
from game_engine.data_pipeline.favor_effect import favor2source
from game_engine.data_pipeline.mood_effect import mood2source
from game_engine.models.shipgirl import ShipGirl



def common_src_modify(source: dict[str, int], npc: ShipGirl) -> dict[str, int]:
    '''对source进行通用修正'''
    # 好感对source修正
    positive_favor_multi, negative_favor_multi = favor2source(npc.favor)

    # 心情对source修正
    mood = npc.get_mood()
    positive_mood_multi, negative_mood_multi = mood2source(mood)

    for k, v in source.items():
        if k in positive_src:
            source[k] = int(v * positive_favor_multi * positive_mood_multi * uniform(0.9, 1.1))
        elif k in negative_src:
            source[k] = int(v * negative_favor_multi * negative_mood_multi * uniform(0.9, 1.1))

    return source
   
    
    