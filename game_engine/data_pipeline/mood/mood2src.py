from config import mood_config
from config.source_config import NEGATIVE_SRC, POSITIVE_SRC


def mood2src(mood: int, source: dict[str, int | float]):
    """心情对source的修正"""
    match mood:
        case mood_config.MOOD_BLISS:
            for k in POSITIVE_SRC:
                source[k] = source[k] * mood_config.BLISS_POSITIVE_K
            for k in NEGATIVE_SRC:
                source[k] = source[k] * mood_config.BLISS_NEGATIVE_K
        case mood_config.MOOD_GOOD:
            for k in POSITIVE_SRC:
                source[k] = source[k] * mood_config.GOOD_POSITIVE_K
            for k in NEGATIVE_SRC:
                source[k] = source[k] * mood_config.GOOD_NEGATIVE_K
        case mood_config.MOOD_BAD:
            for k in POSITIVE_SRC:
                source[k] = source[k] * mood_config.BAD_POSITIVE_K
            for k in NEGATIVE_SRC:
                source[k] = source[k] * mood_config.BAD_NEGATIVE_K
        case _:
            pass
