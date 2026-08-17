from config.chara_config import PLAYER_ID
from config.source_config import POSITIVE_SRC, NEGATIVE_SRC
from game_engine.data_pipeline.abl.abl2src import abl2src
from game_engine.data_pipeline.base.emo_rat2src import emo_rat2src
from game_engine.data_pipeline.favor.favor2src import favor2source
from game_engine.data_pipeline.palam.palam2src import palam2src
from game_engine.data_pipeline.talent.talent2src import talent2src
from game_engine.models.character import Character


def common_src_modify(source: dict[str, int | float], chara: Character) -> dict[str, int]:
    """对source进行通用修正"""
    # 好感对source修正
    if chara.id != PLAYER_ID:
        positive_favor_multi, negative_favor_multi = favor2source(chara.favor)

        for k, v in source.items():
            if k in POSITIVE_SRC:
                source[k] = int(v * positive_favor_multi)
            elif k in NEGATIVE_SRC:
                source[k] = int(v * negative_favor_multi)

    # abl对source修正
    abl2src(chara.abl, source)

    # palam对source修正
    palam2src(chara.palam_lv, source)

    # talent对source修正
    talent2src(chara, source)

    # 约会状态下source的修正
    if chara.id != PLAYER_ID and chara.is_dating():
        source = {k: (source[k] * 1.2) for k in POSITIVE_SRC} | {k: (source[k] * 0.8) for k in NEGATIVE_SRC}

    # 情绪&理性对source的修正
    if chara.id != PLAYER_ID:
        emo_rat2src(chara, source)

    return {k: int(v) for k, v in source.items()}
