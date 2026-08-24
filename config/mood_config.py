MOOD_BLISS = 2
MOOD_GOOD = 1
MOOD_NEUTRAL = 0
MOOD_BAD = -1

MOOD_LABELS = {
    MOOD_BLISS: '幸福',
    MOOD_GOOD: '好心情',
    MOOD_NEUTRAL: '',
    MOOD_BAD: '愤怒'
}

MOOD_COLORS = {
    MOOD_BLISS: '#ffd400',
    MOOD_GOOD: '#66ccff',
    MOOD_NEUTRAL: '',
    MOOD_BAD: '#ff0000'
}


# 每日心情概率
MOOD_GOOD_RATE = 0.1
MOOD_NEUTRAL_RATE = 0.8
MOOD_BAD_RATE = 0.1

# 算法参数
MOOD_HALF_SATURATION = 30000
MOOD_MAX_PROB = 90

# 心情随时间向平静衰减的基础周期（分钟）
MOOD_DECAY_INTERVAL = 120

# 心情对source的修正参数
BLISS_POSITIVE_K = 1.5  # 幸福对正向source的修正参数
GOOD_POSITIVE_K = 1.2   # 好心情对正向source的修正参数
BAD_POSITIVE_K = 0.8    # 愤怒对正向source的修正参数
BLISS_NEGATIVE_K = 0.7  # 幸福对负向source的修正参数
GOOD_NEGATIVE_K = 0.9   # 好心情对负向source的修正参数
BAD_NEGATIVE_K = 1.5    # 愤怒对负向source的修正参数