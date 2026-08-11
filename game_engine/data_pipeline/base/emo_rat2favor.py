def emo_rat2favor(emotion: int, rationality: int):
    """情绪&理性对好感的修正"""
    favor_delta = 0
    if 200 <= emotion < 500:
        favor_delta += 1
    elif 500 <= emotion < 800:
        favor_delta += 2
    elif emotion >= 800:
        favor_delta += 3

    if rationality < 500:
        favor_delta += 2
    elif 500 <= rationality < 800:
        favor_delta += 1

    return favor_delta