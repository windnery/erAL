EXCEPT_MAPPING = {
    # key只能和value共存
    # dating_day：记录约会开始的游戏日，用于跨夜后判断约会是否超时
    'sleeping': ['secretary_ship', 'dating', 'dating_day', 'have_dated_today', 'tired']
}

NOT_MAPPING = {
    # key不能和value共存
    'working': ['secretary_ship', 'dating', 'resting'],
    'free': ['sleeping', 'working', 'following', 'secretary_ship_following', 'dating_following', 'resting']
}

ATTACH_MAPPING = {
    # value是key的附属cflag
    'secretary_ship': ['secretary_ship_following'],
    'dating': ['dating_following']
}
