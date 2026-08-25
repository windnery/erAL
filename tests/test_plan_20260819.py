from game_engine.commands._context import CommandContext
from world import World


def test_dorm_maps_and_travel_times():
    world = World()
    regions = world.map_manager.regions
    assert set(regions) >= {
        "eagle_union_dorm", "ironblood_dorm", "royal_dorm", "sakura_dorm"
    }
    assert world.map_manager.get_available_nodes(
        "eagle_union_dorm", "corridor"
    )[0]["time"] == 1
    assert world.map_manager.get_available_regions(
        "eagle_union_dorm"
    )[0]["time"] == 3


def test_shipgirl_locations_and_colors_are_migrated():
    world = World()
    expected = {
        "laffey": ("eagle_union_dorm", "laffey_room", "#FFB6C1"),
        "Z23": ("ironblood_dorm", "z23_room", "#A9B7C6"),
        "javelin": ("royal_dorm", "javelin_room", "#DDA0DD"),
        "ayanami": ("sakura_dorm", "ayanami_room", "#ffffff"),
        "shiranui": ("sakura_dorm", "shiranui_room", "#ffffff"),
        "akashi": ("sakura_dorm", "akashi_room", "#ffffff"),
    }
    for shipgirl_id, (region, node, color) in expected.items():
        npc = world.npc_manager.shipgirls[shipgirl_id]
        assert npc.location == {"region": region, "node": node}
        assert npc.color == color


def test_shipgirl_daily_recovery_is_silent_and_clamped():
    world = World()
    npc = world.npc_manager.shipgirls["Z23"]
    npc.set_stamina(0)
    npc.set_energy(0)
    world.time_manager.hour = 23
    world.time_manager.minute = 0
    world.player.wake_time = {"hour": 7, "minute": 0}
    pages = world.settle_day(sleep=True)
    assert npc.get_stamina() == npc.base["max_stamina"]
    assert npc.get_energy() == npc.base["max_energy"]
    assert not any("Z23" in page for page in pages)


def test_colored_context_messages_and_state():
    world = World()
    npc = world.npc_manager.shipgirls["laffey"]
    assert world.get_state()["nearby_npcs"] == []
    assert npc.get_state()["color"] == "#FFB6C1"
    ctx = CommandContext(world)
    ctx.say("第一句", "第二句", color=npc.color)
    assert ctx.result() == [
        "[[c:#FFB6C1]]第一句[[/c]]",
        "[[c:#FFB6C1]]第二句[[/c]]",
    ]


def test_old_location_still_loads_in_memory():
    world = World()
    npc = world.npc_manager.shipgirls["Z23"]
    npc.location = {"region": "home", "node": "bedroom"}
    assert world.map_manager.get_current_loc(npc) == "家 · 卧室"