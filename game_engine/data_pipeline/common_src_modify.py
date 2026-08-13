from config.source_config import POSITIVE_SRC, NEGATIVE_SRC
from game_engine.data_pipeline.abl.abl2src import abl2src
from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
from game_engine.data_pipeline.favor.favor2src import favor2source
from game_engine.data_pipeline.palam.palam2src import palam2src
from game_engine.data_pipeline.talent.talent2src import talent2src
from game_engine.models.shipgirl import ShipGirl


def common_src_modify(source: dict[str, int], npc: ShipGirl) -> dict[str, int]:
    """对source进行通用修正"""
    # 好感对source修正
    positive_favor_multi, negative_favor_multi = favor2source(npc.favor)

    for k, v in source.items():
        if k in POSITIVE_SRC:
            source[k] = int(v * positive_favor_multi)
        elif k in NEGATIVE_SRC:
            source[k] = int(v * negative_favor_multi)

    # abl对source修正
    abl2src(npc.abl, source)

    # palam对source修正
    palam2src(npc.palam_lv, source)

    # talent对source修正
    talent2src(npc, source)

    # 约会状态下source的修正
    if npc.is_dating():
        source = {k: (source[k] * 1.2) for k in POSITIVE_SRC} | {k: (source[k] * 0.8) for k in NEGATIVE_SRC}

    # 情绪&理性对source的修正
    emo_rat2src(npc, source)

    return {k: int(v) for k, v in source.items()}
