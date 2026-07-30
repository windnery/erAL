# 对source进行通用修正
from random import uniform

from config.source_kind import POSITIVE_SRC, NEGATIVE_SRC
from game_engine.data_pipeline.favor.favor2src import favor2source
from game_engine.data_pipeline.mood.mood2src import mood2source
from game_engine.data_pipeline.palam.palam2src import palam2src
from game_engine.data_pipeline.talent.talent2src import talent2src
from game_engine.models.shipgirl import ShipGirl



def common_src_modify(source: dict[str, int], npc: ShipGirl) -> dict[str, int]:
    '''对source进行通用修正'''
    # 好感对source修正
    positive_favor_multi, negative_favor_multi = favor2source(npc.favor)

    # 心情对source修正
    mood = npc.get_mood()
    positive_mood_multi, negative_mood_multi = mood2source(mood)

    for k, v in source.items():
        if k in POSITIVE_SRC:
            source[k] = int(v * positive_favor_multi * positive_mood_multi * uniform(0.9, 1.1))
        elif k in NEGATIVE_SRC:
            source[k] = int(v * negative_favor_multi * negative_mood_multi * uniform(0.9, 1.1))

    # palam对source修正
    source = palam2src(npc.palam_lv, source)

    # talent对source修正
    source = talent2src(npc, source)

    # 把source中的float转为int
    for k, v in source.items():
        source[k] = int(v)
        

    return source
   
    
    