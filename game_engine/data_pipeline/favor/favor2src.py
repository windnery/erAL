def favor2source(favor: int) -> tuple[float, float]:
    """好感度对 SOURCE 的全局乘数"""
    if favor < 50:
        positive_favor_multi = 0.9
        negative_favor_multi = 1.1
    elif favor < 100:
        positive_favor_multi = 1.0
        negative_favor_multi = 1.0
    elif favor < 200:
        positive_favor_multi = 1.1
        negative_favor_multi = 0.9
    elif favor < 300:
        positive_favor_multi = 1.2
        negative_favor_multi = 0.8
    elif favor < 500:
        positive_favor_multi = 1.3
        negative_favor_multi = 0.8
    elif favor < 800:
        positive_favor_multi = 1.4
        negative_favor_multi = 0.7
    elif favor < 1000:
        positive_favor_multi = 1.5
        negative_favor_multi = 0.7
    elif favor < 1500:
        positive_favor_multi = 1.6
        negative_favor_multi = 0.6
    elif favor < 2000:
        positive_favor_multi = 1.7
        negative_favor_multi = 0.6
    elif favor < 3000:
        positive_favor_multi = 1.8
        negative_favor_multi = 0.5
    elif favor < 4000:
        positive_favor_multi = 1.9
        negative_favor_multi = 0.5
    else:
        positive_favor_multi = 2.0
        negative_favor_multi = 0.5

    return positive_favor_multi, negative_favor_multi