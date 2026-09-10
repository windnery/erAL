"""json 口上 resolver 与 when 条件求值的单元测试。"""
from __future__ import annotations

import random

from game_engine.dialogue import get_scene
from game_engine.dialogue import _resolver
from game_engine.dialogue._resolver import get_json_scene, match_when
from world import World


def _javelin():
    return World().npc_manager.shipgirls["javelin"]


def test_relationship_match_int_list_and_range():
    c = _javelin()
    c.set_talent("relationship", "3")
    assert match_when(c, {"relationship": 3})
    assert match_when(c, {"relationship": [2, 3]})
    assert match_when(c, {"relationship": {"min": 2, "max": 4}})
    assert not match_when(c, {"relationship": 4})
    assert not match_when(c, {"relationship": {"min": 4}})


def test_flags_dating_and_talents():
    c = _javelin()
    c.cflag["dating"] = True
    assert match_when(c, {"dating": True})
    assert not match_when(c, {"dating": False})
    assert match_when(c, {"flags": {"any": ["dating", "sleeping"]}})
    assert not match_when(c, {"flags": {"not": ["dating"]}})
    c.set_talent("lover", "1")
    assert match_when(c, {"lover": True})
    assert match_when(c, {"talents": {"all": ["lover"]}})


def test_talent_values_marks_mood_favor_trust():
    c = _javelin()
    c.set_talent("sense_of_shame", "0")
    assert match_when(c, {"talent_values": {"sense_of_shame": [0, 1]}})
    assert not match_when(c, {"talent_values": {"sense_of_shame": 2}})
    c.mark["disappointment_mark"] = 1
    assert match_when(c, {"marks": {"disappointment_mark": {"min": 1}}})
    assert not match_when(c, {"marks": {"disappointment_mark": {"min": 2}}})
    c.set_mood(1)
    assert match_when(c, {"mood": 1})
    assert match_when(c, {"mood": {"min": 0, "max": 2}})
    c.favor = 1200
    c.trust = 200
    assert match_when(c, {"favor": {"min": 1000}, "trust": {"min": 100}})


def test_outcome_only_matches_when_passed():
    c = _javelin()
    assert match_when(c, {"outcome": "success"}, outcome="success")
    assert not match_when(c, {"outcome": "success"}, outcome="fail")
    assert not match_when(c, {"outcome": "success"})


def test_unknown_when_key_never_matches():
    c = _javelin()
    assert not match_when(c, {"bogus_key": True})


def test_multiple_keys_are_and():
    c = _javelin()
    c.set_talent("relationship", "3")
    c.cflag["dating"] = False
    assert match_when(c, {"relationship": 3, "dating": False})
    assert not match_when(c, {"relationship": 3, "dating": True})


def _fake_json(variants_a, variants_b, monkeypatch):
    data = {"id": "javelin", "actions": {"talk": [
        {"when": {"relationship": 4}, "variants": variants_a},
        {"variants": variants_b},
    ]}}
    monkeypatch.setattr(_resolver, "load_dialogue", lambda chara_id: data)


def test_json_first_match_wins_and_falls_through(monkeypatch):
    c = _javelin()
    _fake_json([["高好感A"]], [["兜底B"]], monkeypatch)

    c.set_talent("relationship", "4")
    assert get_json_scene(c, "talk") == ["高好感A"]

    c.set_talent("relationship", "1")
    assert get_json_scene(c, "talk") == ["兜底B"]


def test_json_placeholder_rendering(monkeypatch):
    c = _javelin()
    _fake_json([["{name}和{chara}"]], [[]], monkeypatch)
    c.set_talent("relationship", "4")
    assert get_json_scene(c, "talk", player_name="指挥官") == ["指挥官和标枪"]


def test_json_variant_random_choice(monkeypatch):
    c = _javelin()
    _fake_json([["A1"], ["A2"]], [[]], monkeypatch)
    c.set_talent("relationship", "4")
    random.seed(0)
    picked = {tuple(get_json_scene(c, "talk")) for _ in range(60)}
    assert picked == {("A1",), ("A2",)}


def test_json_miss_falls_back_to_python(monkeypatch):
    c = _javelin()
    monkeypatch.setattr(_resolver, "load_dialogue", lambda chara_id: None)
    # javelin 无 json 时走 Python 模块，talk 必有场景
    scene = get_scene(c, "talk", "指挥官")
    assert scene


def test_real_json_first_encounter_uses_placeholder():
    c = _javelin()
    scene = get_scene(c, "first_encounter", "指挥官")
    assert scene
    assert any("指挥官" in m for m in scene)
    assert all("{name}" not in m for m in scene)


def test_json_outcome_branch_selects_fail_scene():
    c = _javelin()
    c.set_talent("relationship", "4")
    fail = get_scene(c, "kiss_i", "指挥官", "fail")
    assert fail and any("不行" in m or "别过" in m for m in fail)
    ok = get_scene(c, "kiss_i", "指挥官", "success")
    assert ok and ok != fail


def test_javelin_covers_entire_contract():
    from config.dialogue_config import ACTION_CONTRACT
    from game_engine.dialogue import get_available_actions

    assert get_available_actions("javelin") == set(ACTION_CONTRACT)


def _laffey():
    return World().npc_manager.shipgirls["laffey"]


LAFFEY_DAILY = [
    "talk", "listen_to_complaints", "relax_together", "work_together",
    "invite_date", "invite_follow", "cancel_follow", "confess", "oath",
]
LAFFEY_INTIMATE = [
    "hug", "body_touch", "kiss_i", "rub_the_head",
    "pinching_cheeks", "poke_the_cheek", "request_a_lap_pillow",
]


def test_laffey_covers_entire_contract_with_content():
    from config.dialogue_config import ACTION_CONTRACT
    from game_engine.dialogue import get_available_actions

    assert get_available_actions("laffey") == set(ACTION_CONTRACT)
    c = _laffey()
    for rel in (0, 2, 4):
        c.set_talent("relationship", str(rel))
        for action in ACTION_CONTRACT:
            assert get_scene(c, action) is not None, (action, rel)


def test_laffey_json_daily_and_intimate_content():
    c = _laffey()
    for rel in (0, 2, 4):
        c.set_talent("relationship", str(rel))
        for action in LAFFEY_DAILY + LAFFEY_INTIMATE:
            assert get_scene(c, action) is not None, (action, rel)


def test_laffey_outcome_branches():
    c = _laffey()
    c.set_talent("relationship", "4")
    fails = {tuple(get_scene(c, "invite_date", "指挥官", "fail")) for _ in range(40)}
    oks = {tuple(get_scene(c, "invite_date", "指挥官", "success")) for _ in range(40)}
    assert fails and oks
    assert fails.isdisjoint(oks)


def test_laffey_uses_chara_specific_voice():
    c = _laffey()
    c.set_talent("relationship", "4")
    scenes = [get_scene(c, "talk") for _ in range(40)]
    assert scenes and any("拉菲" in m for scene in scenes for m in scene)
