def emo_rat2trust(emotion: int, rationality: int):
    """情绪&理性对信赖的修正"""
    trust_delta = 0
    if 200 <= emotion < 500:
        trust_delta += 1
    elif 500 <= emotion < 800:
        trust_delta += 2
    elif emotion >= 800:
        trust_delta += 3

    if rationality < 500:
        trust_delta += 2
    elif 500 <= rationality < 800:
        trust_delta += 1

    return trust_delta