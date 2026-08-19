"""绫波 口上内容（从 data/characters/绫波.json 迁移）。"""


def talk(c):
    """会话"""
    if c.favor <= 30:
        return [
            ["{name}安静地站在原地，轻声开口：「指挥官……有什么吩咐吗？」"],
            ["{name}盯着你看了好一会儿，才小声说：「对不起……绫波不太擅长聊天。」"],
            ["{name}微微低下头：「指挥官愿意和绫波说话，绫波很高兴……真的。」"],
        ]
    return [
        ["{name}的眼神柔和了下来：「和指挥官在一起的时间，很安心……」"],
        ["{name}缓缓地靠近半步：「如果指挥官不嫌弃……绫波想再多陪你一会儿。」"],
    ]


def rub_the_head(c):
    """摸头"""
    return [
        ["{name}身体轻轻一颤，随后静静地闭上了眼睛。"],
        ["{name}的脸泛起红晕，「指挥官的手……很温暖。」"],
    ]


def work_together(c):
    """一起工作"""
    return [["{name}安静地配合着你，偶尔投来一个默默的眼神。"]]


def body_touch(c):
    """身体接触"""
    return [["{name}轻轻一颤，没有躲开，只是垂下了眼帘。"]]


def hug(c):
    """拥抱"""
    return [["{name}被你抱住，小声说：「……暖和。」"]]


def poke_the_cheek(c):
    """戳脸颊"""
    return [["你戳了戳{name}的脸颊，她眨了眨眼，什么都没说。"]]


def pinching_cheeks(c):
    """捏脸颊"""
    return [["你捏了捏{name}的脸，她面无表情地看了你一会儿。"]]


def request_a_lap_pillow(c):
    """膝枕"""
    return [["{name}默默枕到你腿上，安静地闭上了眼睛。"]]


def rub_the_belly(c):
    """摸肚子"""
    return [["{name}摸了摸肚子，小声说：「……不饿。才怪。」"]]


def rub_the_butt(c):
    """摸屁股"""
    return [["你碰到{name}的屁股，她默默挪开了一步，耳朵尖发红。"]]