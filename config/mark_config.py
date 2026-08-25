MARK = {
    'pain_mark': '苦痛刻印',
    'pleasure_mark': '快乐刻印',
    'submission_mark': '屈服刻印',
    'disappointment_mark': '失望刻印'
}

MARK_PAIN = {
    # 苦痛
    1: 2000,
    2: 4000,
    3: 8000
}

# 快乐刻印根据绝顶等级获取 这里不需要设定
# MARK_PLEASURE = {
#     1: 1,
#     2: 2,
#     3: 3
# }

MARK_SUBMISSION = {
    # 恭顺+屈服
    1: 4500,
    2: 7000,
    3: 10000
}

MARK_DISAPPOINTMENT = {
    # 反感+恐怖+抑郁
    1: 600,
    2: 1200,
    3: 2000
}

MARK_PAIN2SRC = {
    1: 1.1,
    2: 1.2,
    3: 1.3
}

MARK_PLEASURE2SRC = {
    1: 1.15,
    2: 1.25,
    3: 1.35
}

MARK_SUBMISSION2POS = {
    1: 1.15,
    2: 1.25,
    3: 1.35
}

MARK_SUBMISSION2NEG = {
    1: 0.75,
    2: 0.6,
    3: 0.4
}

MARK_DISAPPOINTMENT2POS = {
    1: 0.75,
    2: 0.5,
    3: 0.1
}

MARK_DISAPPOINTMENT2NEG = {
    1: 1.5,
    2: 2.0,
    3: 3.0
}