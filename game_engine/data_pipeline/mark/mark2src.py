from config.mark_config import MARK_PAIN2SRC, MARK_PLEASURE2SRC, MARK_SUBMISSION2POS, MARK_SUBMISSION2NEG, \
    MARK_DISAPPOINTMENT2POS, MARK_DISAPPOINTMENT2NEG


def mark2src(mark: dict[str, int], source: dict[str, int | float]):
    """mark对source的修正（刻印可共存，多个刻印效果同时叠加）"""
    if mark.get('pain_mark', 0) > 0:
        source['pain_source'] *= MARK_PAIN2SRC[mark['pain_mark']]
        source['fear_source'] *= MARK_PAIN2SRC[mark['pain_mark']]
    if mark.get('pleasure_mark', 0) > 0:
        source['lust_source'] *= MARK_PLEASURE2SRC[mark['pleasure_mark']]
        source['achievement_source'] *= MARK_PLEASURE2SRC[mark['pleasure_mark']]
    if mark.get('submission_mark', 0) > 0:
        source['obedience_source'] *= MARK_SUBMISSION2POS[mark['submission_mark']]
        source['submission_source'] *= MARK_SUBMISSION2POS[mark['submission_mark']]
        source['disgust_source'] *= MARK_SUBMISSION2NEG[mark['submission_mark']]
    if mark.get('disappointment_mark', 0) > 0:
        source['obedience_source'] *= MARK_DISAPPOINTMENT2POS[mark['disappointment_mark']]
        source['disgust_source'] *= MARK_DISAPPOINTMENT2NEG[mark['disappointment_mark']]
