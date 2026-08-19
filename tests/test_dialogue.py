import pytest

from game_engine.commands._common import say_chara_line
from game_engine.commands._context import CommandContext
from game_engine.dialogue import get_scene
from world import World

CORE_DAILY = [
    "talk", "rub_the_head", "work_together", "body_touch", "hug",
    "poke_the_cheek", "pinching_cheeks", "request_a_lap_pillow",
    "rub_the_belly", "rub_the_butt", "invite_date", "end_date",
]

TRAIN_ACTIONS = [
    "kiss", "caress", "breast_caress", "breast_massage", "nipple_caress",
    "nipple_sucking", "finger_insert", "lick_pussy", "lick_ass",
    "ass_caress", "spread_the_ass", "spread_the_labia",
    "common_position", "ejaculation",
]


def _distinct_scenes(world, chara_id, action, rel, dating=False, samples=60, favor=None):
    c = world.npc_manager.shipgirls[chara_id]
    c.cflag["dating"] = dating
    if favor is not None:
        c.favor = favor
    c.set_talent("relationship", str(rel))
    return {tuple(get_scene(c, action)) for _ in range(samples)}


def test_laffey_daily_actions_three_scenes_per_tier():
    world = World()
    for rel in (0, 2, 4):
        for action in CORE_DAILY:
            scenes = _distinct_scenes(world, "laffey", action, rel)
            assert len(scenes) >= 3, (action, rel, len(scenes))


def test_javelin_daily_actions_three_scenes_per_tier():
    world = World()
    for rel in (0, 2, 4):
        for action in CORE_DAILY:
            scenes = _distinct_scenes(world, "javelin", action, rel)
            assert len(scenes) >= 3, (action, rel, len(scenes))


def test_talk_tiers_are_distinct():
    world = World()
    low = _distinct_scenes(world, "laffey", "talk", 0)
    mid = _distinct_scenes(world, "laffey", "talk", 2)
    high = _distinct_scenes(world, "laffey", "talk", 4)
    assert low.isdisjoint(mid)
    assert mid.isdisjoint(high)
    assert low.isdisjoint(high)


def test_talk_dating_branch_is_distinct():
    world = World()
    dating = _distinct_scenes(world, "laffey", "talk", 2, dating=True)
    normal = _distinct_scenes(world, "laffey", "talk", 2, dating=False)
    assert dating
    assert dating.isdisjoint(normal)


def test_confess_oath_push_down_have_content():
    world = World()
    for chara_id in ("laffey", "javelin"):
        assert len(_distinct_scenes(world, chara_id, "confess", 2)) >= 1
        assert len(_distinct_scenes(world, chara_id, "oath", 4)) >= 1
        assert len(_distinct_scenes(world, chara_id, "push_down", 2)) >= 1


def test_get_scene_laffey_common_position_favor_gate():
    world = World()
    laffey = world.npc_manager.shipgirls["laffey"]
    laffey.favor = 100
    assert get_scene(laffey, "common_position") is None
    laffey.favor = 900
    scene = get_scene(laffey, "common_position")
    assert scene
    assert all(isinstance(msg, str) and msg for msg in scene)


def test_laffey_train_actions_three_scenes_per_tier():
    world = World()
    for rel in (0, 2, 4):
        for action in TRAIN_ACTIONS:
            scenes = _distinct_scenes(world, "laffey", action, rel, favor=900)
            assert len(scenes) >= 3, (action, rel, len(scenes))


def test_javelin_train_actions_three_scenes_per_tier():
    world = World()
    for rel in (0, 2, 4):
        for action in TRAIN_ACTIONS:
            scenes = _distinct_scenes(world, "javelin", action, rel, favor=900)
            assert len(scenes) >= 3, (action, rel, len(scenes))


def test_defloration_first_time_has_multiple_scenes():
    world = World()
    laffey = world.npc_manager.shipgirls["laffey"]
    laffey.set_exp("v_insert_exp", 0)
    scenes = {tuple(get_scene(laffey, "defloration")) for _ in range(60)}
    assert len(scenes) >= 3


def test_defloration_repeat_returns_fallback():
    world = World()
    javelin = world.npc_manager.shipgirls["javelin"]
    javelin.set_exp("v_insert_exp", 5)
    assert get_scene(javelin, "defloration") is not None


def test_get_scene_Z23_talk_variants():
    world = World()
    z23 = world.npc_manager.shipgirls["Z23"]
    z23.favor = 10
    assert get_scene(z23, "talk") in [
        ["{name}合上手中的书，认真地看向你，「指挥官，是有任务要下达吗？」"],
        ["{name}推了推不存在的眼镜，「闲聊……吗？如果是工作上的事情，我随时可以回答。」"],
        ["{name}正在笔记本上写着什么，「稍等，让我把今天的训练记录整理完。」"],
    ]


def test_get_scene_ayanami_talk_variants():
    world = World()
    ayanami = world.npc_manager.shipgirls["ayanami"]
    ayanami.favor = 100
    assert get_scene(ayanami, "talk") in [
        ["{name}的眼神柔和了下来：「和指挥官在一起的时间，很安心……」"],
        ["{name}缓缓地靠近半步：「如果指挥官不嫌弃……绫波想再多陪你一会儿。」"],
    ]


def test_get_scene_unknown_action_returns_none():
    world = World()
    laffey = world.npc_manager.shipgirls["laffey"]
    assert get_scene(laffey, "no_such_action") is None


def test_get_scene_chara_without_module_returns_none():
    world = World()
    shiranui = world.npc_manager.shipgirls["shiranui"]
    assert get_scene(shiranui, "talk") is None


def test_say_chara_line_colored_and_name_replaced():
    world = World()
    laffey = world.npc_manager.shipgirls["laffey"]
    laffey.favor = 900
    ctx = CommandContext(world)
    say_chara_line(laffey, ctx, "common_position")
    msgs = ctx.result()
    assert msgs
    assert all(msg.startswith("[[c:#FFB6C1]]") for msg in msgs)
    assert all("{name}" not in msg for msg in msgs)
    assert any("拉菲" in msg for msg in msgs)


def test_say_chara_line_multi_message_scene_all_colored(monkeypatch):
    world = World()
    laffey = world.npc_manager.shipgirls["laffey"]
    import game_engine.dialogue.laffey as laffey_mod

    monkeypatch.setattr(laffey_mod, "body_touch", lambda c: [["第一句", "第二句", "第三句"]])
    ctx = CommandContext(world)
    say_chara_line(laffey, ctx, "body_touch")
    assert ctx.result() == [
        "[[c:#FFB6C1]]第一句[[/c]]",
        "[[c:#FFB6C1]]第二句[[/c]]",
        "[[c:#FFB6C1]]第三句[[/c]]",
    ]


def test_say_chara_line_silent_when_no_scene():
    world = World()
    laffey = world.npc_manager.shipgirls["laffey"]
    ctx = CommandContext(world)
    say_chara_line(laffey, ctx, "no_such_action")
    assert ctx.result() == []


def test_shipgirl_no_longer_holds_lines():
    world = World()
    npc = world.npc_manager.shipgirls["laffey"]
    assert not hasattr(npc, "lines")