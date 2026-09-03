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


def test_javelin_daily_actions_have_content():
    world = World()
    for rel in (0, 2, 4):
        for action in CORE_DAILY:
            scenes = _distinct_scenes(world, "javelin", action, rel)
            assert len(scenes) >= 1, (action, rel, len(scenes))


def test_javelin_train_actions_have_content():
    world = World()
    for rel in (0, 2, 4):
        for action in TRAIN_ACTIONS:
            scenes = _distinct_scenes(world, "javelin", action, rel, favor=900)
            assert len(scenes) >= 1, (action, rel, len(scenes))


def test_confess_oath_push_down_have_content():
    world = World()
    assert len(_distinct_scenes(world, "javelin", "confess", 2)) >= 1
    assert len(_distinct_scenes(world, "javelin", "oath", 4)) >= 1
    assert len(_distinct_scenes(world, "javelin", "push_down", 2)) >= 1


def test_defloration_repeat_returns_fallback():
    world = World()
    javelin = world.npc_manager.shipgirls["javelin"]
    javelin.set_exp("v_insert_exp", 5)
    assert get_scene(javelin, "defloration") is not None


def test_get_scene_unknown_action_returns_none():
    world = World()
    javelin = world.npc_manager.shipgirls["javelin"]
    assert get_scene(javelin, "no_such_action") is None


def test_get_scene_chara_without_module_returns_none():
    world = World()
    shiranui = world.npc_manager.shipgirls["shiranui"]
    assert get_scene(shiranui, "talk") is None


def test_say_chara_line_colored_and_name_replaced():
    world = World()
    javelin = world.npc_manager.shipgirls["javelin"]
    javelin.set_talent("relationship", "4")
    ctx = CommandContext(world)
    say_chara_line(javelin, ctx, "common_position")
    msgs = ctx.result()
    assert msgs
    assert all(msg.startswith("[[c:#DDA0DD]]") for msg in msgs)
    assert all("{name}" not in msg and "{player_name}" not in msg for msg in msgs)
    assert any("标枪" in msg for msg in msgs)


def test_say_chara_line_multi_message_scene_all_colored(monkeypatch):
    world = World()
    javelin = world.npc_manager.shipgirls["javelin"]
    import game_engine.dialogue.javelin as javelin_mod

    monkeypatch.setattr(javelin_mod, "body_touch", lambda c: [["第一句", "第二句", "第三句"]])
    ctx = CommandContext(world)
    say_chara_line(javelin, ctx, "body_touch")
    assert ctx.result() == [
        "[[c:#DDA0DD]]第一句[[/c]]",
        "[[c:#DDA0DD]]第二句[[/c]]",
        "[[c:#DDA0DD]]第三句[[/c]]",
    ]


def test_say_chara_line_silent_when_no_scene():
    world = World()
    javelin = world.npc_manager.shipgirls["javelin"]
    ctx = CommandContext(world)
    say_chara_line(javelin, ctx, "no_such_action")
    assert ctx.result() == []


def test_shipgirl_no_longer_holds_lines():
    world = World()
    npc = world.npc_manager.shipgirls["javelin"]
    assert not hasattr(npc, "lines")